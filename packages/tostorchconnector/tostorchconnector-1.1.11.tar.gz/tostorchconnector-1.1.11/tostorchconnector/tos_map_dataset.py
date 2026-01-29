import logging
from functools import partial
from typing import Any, Callable, Iterator, Optional, List, Union

import torch

from . import TosObjectReader
from .tos_client import CredentialProvider, TosClientConfig, TosClient, ReaderType
from .tos_common import default_trans, gen_dataset_from_prefix, \
    gen_dataset_from_urls, trans_to_tos_object_reader
from .tos_object_meta import TosObjectMeta

log = logging.getLogger(__name__)


class TosMapDataset(torch.utils.data.Dataset):
    def __init__(self, region: str,
                 gen_dataset: Callable[[TosClient], Iterator[TosObjectMeta]],
                 endpoint: Optional[str] = None,
                 transform: Callable[[TosObjectReader], Any] = default_trans,
                 cred: Optional[CredentialProvider] = None,
                 client_conf: Optional[TosClientConfig] = None,
                 use_native_client: bool = True,
                 reader_type: Optional[ReaderType] = None,
                 buffer_size: Optional[int] = None,
                 enable_crc: bool = True,
                 prefetch_concurrency: int = 0):
        self._gen_dataset = gen_dataset
        self._region = region
        self._endpoint = endpoint
        self._trans = transform
        self._cred = cred
        self._client_conf = client_conf
        self._from_urls = False
        self._dataset: Optional[List[TosObjectMeta]] = None
        self._reader_type = reader_type
        self._buffer_size = buffer_size
        self._prefetch_concurrency = prefetch_concurrency
        self._client = TosClient(self._region, self._endpoint, self._cred, self._client_conf,
                                 use_native_client, enable_crc)
        log.info('TosMapDataset init tos client succeed')

    @classmethod
    def from_urls(cls, urls: Union[str, Iterator[str]], *, region: str, endpoint: Optional[str] = None,
                  transform: Callable[[TosObjectReader], Any] = default_trans,
                  cred: Optional[CredentialProvider] = None,
                  client_conf: Optional[TosClientConfig] = None,
                  use_native_client: bool = True,
                  reader_type: Optional[ReaderType] = None,
                  buffer_size: Optional[int] = None,
                  enable_crc: bool = True,
                  prefetch_concurrency: int = 0):
        log.info(f'building {cls.__name__} from_urls')
        dataset = cls(region, partial(gen_dataset_from_urls, urls), endpoint, transform, cred,
                      client_conf, use_native_client, reader_type, buffer_size, enable_crc, prefetch_concurrency)

        dataset._from_urls = True
        return dataset

    @classmethod
    def from_prefix(cls, prefix: str, *, region: str, endpoint: Optional[str] = None,
                    transform: Callable[[TosObjectReader], Any] = default_trans,
                    cred: Optional[CredentialProvider] = None,
                    client_conf: Optional[TosClientConfig] = None,
                    use_native_client: bool = True,
                    reader_type: Optional[ReaderType] = None,
                    buffer_size: Optional[int] = None,
                    enable_crc: bool = True,
                    prefetch_concurrency: int = 0):
        log.info(f'building {cls.__name__} from_prefix')
        return cls(region, partial(gen_dataset_from_prefix, prefix), endpoint, transform, cred,
                   client_conf, use_native_client, reader_type, buffer_size, enable_crc, prefetch_concurrency)

    def __getitem__(self, i: int) -> Any:
        return self._trans_tos_object(i)

    def __getitems__(self, idxs: List[int]) -> List[Any]:
        if self._client.use_native_client:
            object_metas = []
            for i in idxs:
                object_meta = self._data_set[i]
                object_metas.append(
                    (object_meta.bucket, object_meta.key, object_meta.etag, object_meta.size, object_meta.crc64))
            return [self._trans(obj) for obj in
                    self._client.batch_get_objects(object_metas, self._reader_type, self._buffer_size,
                                                   self._prefetch_concurrency,
                                                   self._prefetch_concurrency <= 0 and self._from_urls)]

        return [self._trans_tos_object(i) for i in idxs]

    def __len__(self) -> int:
        return len(self._data_set)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            try:
                log.info(f'exception occurred before closing tos client: {exc_type.__name__}: {exc_val}')
            except:
                pass
            finally:
                self.close()
        else:
            self.close()

    @property
    def _data_set(self) -> List[TosObjectMeta]:
        if self._dataset is None:
            self._dataset = list(self._gen_dataset(self._client))

        assert self._dataset is not None
        return self._dataset

    def _trans_tos_object(self, i: int) -> Any:
        object_meta = self._data_set[i]
        obj = trans_to_tos_object_reader(object_meta, self._client, reader_type=self._reader_type,
                                         buffer_size=self._buffer_size)
        return self._trans(obj)
