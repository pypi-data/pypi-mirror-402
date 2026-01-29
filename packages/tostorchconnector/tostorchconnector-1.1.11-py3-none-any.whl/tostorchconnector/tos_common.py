import logging
from typing import Union, Iterator, Tuple, Optional, List
import os
from . import TosObjectReader
from .tos_client import TosClient, ReaderType
from .tos_object_meta import TosObjectMeta
from tosnativeclient import init_tracing_log

log = logging.getLogger(__name__)


def init_log(level: str = '', directory: str = '',
             file_name_prefix: str = '') -> None:
    init_tracing_log(level, directory, file_name_prefix + '-' + str(os.getpid()))


class TosObjectIterable(object):
    def __init__(self, bucket: str, prefix: str, client: TosClient, prefetch_concurrency: int = 0,
                 distributed_info: Optional[Tuple[int, int, int, int]] = None):
        self._bucket = bucket
        self._prefix = prefix
        self._list_background_buffer_count = 3
        self._client = client
        self._prefetch_concurrency = prefetch_concurrency
        self._distributed_info = distributed_info

    def __iter__(self) -> Iterator[TosObjectMeta]:
        return iter(TosObjectIterator(self._bucket, self._prefix, self._list_background_buffer_count,
                                      self._client, self._prefetch_concurrency, self._distributed_info))


class TosObjectIterator(object):
    def __init__(self, bucket: str, prefix: str, list_background_buffer_count: int, client: TosClient,
                 prefetch_concurrency: int = 0,
                 distributed_info: Optional[Tuple[int, int, int, int]] = None):
        self._bucket = bucket
        self._prefix = prefix
        self._list_background_buffer_count = list_background_buffer_count
        self._prefetch_concurrency = prefetch_concurrency
        self._distributed_info = distributed_info
        self._client = client
        self._delimiter: Optional[str] = None
        self._continuation_token: Optional[str] = None

        self._list_stream = None
        self._object_metas = None
        self._native_object_streams = None
        self._index = 0
        self._is_truncated = True

    def close(self) -> None:
        if self._list_stream is not None:
            self._list_stream.close()

    def __iter__(self) -> Iterator[TosObjectMeta]:
        return self

    def __next__(self) -> TosObjectMeta:
        if self._client.use_native_client:
            if self._list_stream is None:
                self._list_stream = self._client.gen_list_stream(self._bucket, self._prefix, max_keys=1000,
                                                                 delimiter=self._delimiter,
                                                                 continuation_token=self._continuation_token,
                                                                 list_background_buffer_count=self._list_background_buffer_count,
                                                                 prefetch_concurrency=self._prefetch_concurrency,
                                                                 distributed_info=self._distributed_info)
            if self._object_metas is None or self._index >= len(self._object_metas):
                self._object_metas = None
                self._index = 0
                while 1:
                    try:
                        (objects, native_object_streams) = next(self._list_stream)
                    except Exception:
                        self.close()
                        raise
                    self._continuation_token = self._list_stream.current_continuation_token()
                    self._object_metas = objects.contents
                    self._native_object_streams = native_object_streams
                    if self._object_metas is not None and len(self._object_metas) > 0:
                        break
            object_meta = self._object_metas[self._index]
            native_object_stream = None
            if self._native_object_streams is not None:
                native_object_stream = self._native_object_streams[self._index]
            self._index += 1
            # this is very critical use the original bucket
            object_meta = TosObjectMeta(self._bucket, object_meta.key, object_meta.size, object_meta.etag,
                                        object_meta.crc64)
            object_meta._native_object_stream = native_object_stream
            return object_meta

        while self._object_metas is None or self._index >= len(self._object_metas):
            if not self._is_truncated:
                raise StopIteration
            self._object_metas, self._is_truncated, self._continuation_token = self._client.list_objects(
                self._bucket,
                self._prefix,
                max_keys=1000,
                continuation_token=self._continuation_token,
                delimiter=self._delimiter)
            self._index = 0

        object_meta = self._object_metas[self._index]
        self._index += 1
        return object_meta


class TosBatchGetObjectsIterator(object):
    def __init__(self, object_metas: Iterator[Tuple[str, str, Optional[str], Optional[int], Optional[int]]],
                 client: TosClient, reader_type: Optional[ReaderType] = None,
                 buffer_size: Optional[int] = None, prefetch_concurrency: int = 0,
                 fetch_etag_size: bool = False):
        self._object_metas = object_metas
        self._client = client
        self._reader_type = reader_type
        self._buffer_size = buffer_size
        self._prefetch_concurrency = prefetch_concurrency
        self._fetch_etag_size = fetch_etag_size
        self._batch_size = self._prefetch_concurrency if self._prefetch_concurrency > 0 else 256
        self._tos_object_readers = None
        self._index = 0
        self._has_next = True

    def __iter__(self) -> Iterator[TosObjectReader]:
        return self

    def __next__(self) -> TosObjectReader:
        if self._tos_object_readers is None or self._index >= len(self._tos_object_readers):
            if not self._has_next:
                raise StopIteration
            tos_object_readers = self.batch_get_objects()
            if tos_object_readers is None:
                raise StopIteration
            self._tos_object_readers = tos_object_readers
            self._index = 0

        tos_object_reader = self._tos_object_readers[self._index]
        self._index += 1
        return tos_object_reader

    def batch_get_objects(self) -> Optional[List[TosObjectReader]]:
        object_metas = []
        while len(object_metas) < self._batch_size:
            try:
                object_meta = next(self._object_metas)
                object_metas.append(object_meta)
            except StopIteration:
                self._has_next = False
                break

        if len(object_metas) > 0:
            tos_object_readers = self._client.batch_get_objects(object_metas, reader_type=self._reader_type,
                                                                buffer_size=self._buffer_size,
                                                                prefetch_concurrency=self._prefetch_concurrency,
                                                                fetch_etag_size=self._fetch_etag_size)
            assert len(tos_object_readers) == len(object_metas)
            return tos_object_readers

        return None


def parse_tos_url(url: str) -> Tuple[str, str]:
    if not url:
        raise ValueError('url is empty')

    if url.startswith('tos://'):
        url = url[len('tos://'):]

    if not url:
        raise ValueError('bucket is empty')

    url = url.split('/', maxsplit=1)
    if len(url) == 1:
        bucket = url[0]
        prefix = ''
    else:
        bucket = url[0]
        prefix = url[1]

    if not bucket:
        raise ValueError('bucket is empty')
    return bucket, prefix


def default_trans(obj: TosObjectReader) -> TosObjectReader:
    return obj


def gen_dataset_from_urls(urls: Union[str, Iterator[str]], _: TosClient, prefetch_concurrency: int = 0,
                          distributed_info: Optional[Tuple[int, int, int, int]] = None) -> Iterator[TosObjectMeta]:
    if isinstance(urls, str):
        urls = [urls]
    return (TosObjectMeta(bucket, key) for bucket, key in (parse_tos_url(url) for url in urls))


def gen_dataset_from_prefix(prefix: str, client: TosClient, prefetch_concurrency: int = 0,
                            distributed_info: Optional[Tuple[int, int, int, int]] = None) -> Iterator[TosObjectMeta]:
    bucket, prefix = parse_tos_url(prefix)
    return iter(TosObjectIterable(bucket, prefix, client, prefetch_concurrency, distributed_info))


def trans_to_tos_object_reader(object_meta: TosObjectMeta, client: TosClient, reader_type: Optional[ReaderType] = None,
                               buffer_size: Optional[int] = None, preload: bool = False) -> TosObjectReader:
    return client.get_object(object_meta.bucket, object_meta.key, object_meta.etag, object_meta.size,
                             reader_type=reader_type, buffer_size=buffer_size, preload=preload, crc64=object_meta.crc64)


def path_or_str_to_str(path: Union[str, os.PathLike]) -> str:
    return path if isinstance(path, str) else str(path)
