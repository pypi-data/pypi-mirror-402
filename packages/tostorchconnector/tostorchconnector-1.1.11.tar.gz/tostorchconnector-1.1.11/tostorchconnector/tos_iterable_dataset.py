import logging
from functools import partial
from typing import Iterator, Any, Optional, Callable, Union, Tuple

import torch

from . import TosObjectReader
from .tos_client import CredentialProvider, TosClientConfig, TosClient, ReaderType
from .tos_common import default_trans, gen_dataset_from_urls, gen_dataset_from_prefix, trans_to_tos_object_reader, \
    TosBatchGetObjectsIterator
from .tos_object_meta import TosObjectMeta

log = logging.getLogger(__name__)


class TosIterableDataset(torch.utils.data.IterableDataset):
    def __init__(self, region: str,
                 gen_dataset: Callable[[TosClient, int, Optional[Tuple[int, int, int, int]]], Iterator[TosObjectMeta]],
                 endpoint: Optional[str] = None,
                 transform: Callable[[TosObjectReader], Any] = default_trans,
                 cred: Optional[CredentialProvider] = None,
                 client_conf: Optional[TosClientConfig] = None,
                 sharding: bool = False,
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
        self._sharding = sharding
        self._from_urls = False
        if torch.distributed.is_initialized():
            self._rank = torch.distributed.get_rank()
            self._world_size = torch.distributed.get_world_size()
        else:
            self._rank = 0
            self._world_size = 1
        self._reader_type = reader_type
        self._buffer_size = buffer_size
        self._prefetch_concurrency = prefetch_concurrency
        self._client = TosClient(self._region, self._endpoint, self._cred, self._client_conf,
                                 use_native_client, enable_crc)
        log.info('TosIterableDataset init tos client succeed')

    @classmethod
    def from_urls(cls, urls: Union[str, Iterator[str]], *, region: str, endpoint: Optional[str] = None,
                  transform: Callable[[TosObjectReader], Any] = default_trans,
                  cred: Optional[CredentialProvider] = None,
                  client_conf: Optional[TosClientConfig] = None,
                  sharding: bool = False,
                  use_native_client: bool = True,
                  reader_type: Optional[ReaderType] = None,
                  buffer_size: Optional[int] = None,
                  enable_crc: bool = True,
                  prefetch_concurrency: int = 0):
        log.info(f'building {cls.__name__} from_urls')
        dataset = cls(region, partial(gen_dataset_from_urls, urls), endpoint, transform, cred, client_conf,
                      sharding, use_native_client, reader_type, buffer_size, enable_crc, prefetch_concurrency)
        dataset._from_urls = True
        return dataset

    @classmethod
    def from_prefix(cls, prefix: str, *, region: str, endpoint: Optional[str] = None,
                    transform: Callable[[TosObjectReader], Any] = default_trans,
                    cred: Optional[CredentialProvider] = None,
                    client_conf: Optional[TosClientConfig] = None,
                    sharding: bool = False,
                    use_native_client: bool = True,
                    reader_type: Optional[ReaderType] = None,
                    buffer_size: Optional[int] = None,
                    enable_crc: bool = True,
                    prefetch_concurrency: int = 0):
        log.info(f'building {cls.__name__} from_prefix')
        return cls(region, partial(gen_dataset_from_prefix, prefix), endpoint, transform, cred,
                   client_conf, sharding, use_native_client, reader_type, buffer_size, enable_crc, prefetch_concurrency)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            try:
                log.info(f'Exception occurred before closing tos client: {exc_type.__name__}: {exc_val}')
            except:
                pass
            finally:
                self.close()
        else:
            self.close()

    def __iter__(self) -> Iterator[Any]:
        worker_id = 0
        worker_size = 1
        if self._sharding:
            worker_info = torch.utils.data.get_worker_info()
            if worker_info is not None:
                worker_id = worker_info.id
                worker_size = worker_info.num_workers

        if self._client.use_native_client:
            distribute_info = (self._world_size, self._rank, worker_size, worker_id)
            if not self._sharding or (self._world_size == 1 and worker_size == 1):
                distribute_info = None

            if self._prefetch_concurrency > 0:
                if self._from_urls:
                    part_dataset = (
                        obj
                        for idx, obj in enumerate(self._gen_dataset(self._client, 0, None))
                        if idx % self._world_size == self._rank
                    )
                    object_metas = (
                        (obj.bucket, obj.key, obj.etag, obj.size, obj.crc64)
                        for idx, obj in enumerate(part_dataset)
                        if idx % worker_size == worker_id
                    )
                    return (self._trans(obj) for obj in
                            TosBatchGetObjectsIterator(object_metas, self._client, self._reader_type, self._buffer_size,
                                                       self._prefetch_concurrency))

                native_object_streams = (obj._native_object_stream for obj in
                                         self._gen_dataset(self._client, self._prefetch_concurrency, distribute_info))

                return map(
                    self._trans,
                    self._client._trans_to_object_readers(native_object_streams, self._reader_type, self._buffer_size),
                )

            if self._from_urls:
                part_dataset = (
                    obj
                    for idx, obj in enumerate(self._gen_dataset(self._client, 0, None))
                    if idx % self._world_size == self._rank
                )
                object_metas = (
                    (obj.bucket, obj.key, obj.etag, obj.size, obj.crc64)
                    for idx, obj in enumerate(part_dataset)
                    if idx % worker_size == worker_id
                )
                return (self._trans(obj) for obj in
                        TosBatchGetObjectsIterator(object_metas, self._client, self._reader_type, self._buffer_size,
                                                   self._prefetch_concurrency, True))

            return map(self._trans_tos_object,
                       self._gen_dataset(self._client, self._prefetch_concurrency, distribute_info))

        if not self._sharding or (self._world_size == 1 and worker_size == 1):
            return map(self._trans_tos_object, self._gen_dataset(self._client, 0, None))

        part_dataset = (
            obj
            for idx, obj in enumerate(self._gen_dataset(self._client, 0, None))
            if idx % self._world_size == self._rank
        )
        part_dataset = (
            obj
            for idx, obj in enumerate(part_dataset)
            if idx % worker_size == worker_id
        )
        return map(self._trans_tos_object, part_dataset)

    def _trans_tos_object(self, object_meta: TosObjectMeta) -> Any:
        obj = trans_to_tos_object_reader(object_meta, self._client, reader_type=self._reader_type,
                                         buffer_size=self._buffer_size)
        return self._trans(obj)
