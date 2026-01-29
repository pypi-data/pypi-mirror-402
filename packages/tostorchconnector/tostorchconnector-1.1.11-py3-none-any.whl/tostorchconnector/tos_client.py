import atexit
import enum
import logging
import multiprocessing
import os
import gc

from functools import partial
from typing import Optional, List, Tuple, Any, Iterator

import tos
import tosnativeclient
from tosnativeclient import ReadStream

from . import TosObjectWriter, TosObjectReader
from .tos_object_meta import TosObjectMeta
from .tos_object_reader import _TosObjectStream, RangedTosObjectReader, DirectTosObjectReader, SequentialTosObjectReader
from .tos_object_writer import PutObjectStream

log = logging.getLogger(__name__)

import threading
import weakref
import traceback

_client_lock = threading.Lock()
_client_map = weakref.WeakSet()


def _before_fork():
    with _client_lock:
        clients = list(_client_map)

    if not clients or len(clients) == 0:
        return

    try:
        for client in clients:
            if client._inner_client is not None:
                if hasattr(client._inner_client, 'close') and callable(client._inner_client.close):
                    client._inner_client.close()
                client._inner_client = None
        _reset_client_map()
        gc.collect()
    except Exception as e:
        log.warning(f'failed to clean up native clients before fork, {str(e)}')
        traceback.print_exc()


def _after_fork_in_child():
    _reset_client_map()


def _reset_client_map():
    global _client_map
    with _client_lock:
        _client_map = weakref.WeakSet()


os.register_at_fork(before=_before_fork, after_in_child=_after_fork_in_child)


def tear_down():
    with _client_lock:
        clients = list(_client_map)

    if not clients or len(clients) == 0:
        return

    try:
        for client in clients:
            if client._inner_client is not None:
                if hasattr(client._inner_client, 'close') and callable(client._inner_client.close):
                    client._inner_client.close()
                client._inner_client = None
    except Exception as e:
        log.warning(f'failed to clean up native clients before atexit, {str(e)}')
        traceback.print_exc()


atexit.register(tear_down)


class ReaderType(enum.Enum):
    SEQUENTIAL = 'Sequential'
    RANGED = 'Ranged'
    DIRECT = 'Direct'


class CredentialProvider(object):
    def __init__(self, ak: str, sk: str):
        self._ak = ak
        self._sk = sk

    @property
    def ak(self) -> str:
        return self._ak

    @property
    def sk(self) -> str:
        return self._sk


class TosClientConfig(object):
    def __init__(self, part_size: int = 8 * 1024 * 1024,
                 max_retry_count: int = 3, shared_prefetch_tasks: int = 32, shared_upload_part_tasks: int = 32):
        self._part_size = part_size
        self._max_retry_count = max_retry_count
        self._shared_prefetch_tasks = shared_prefetch_tasks
        self._shared_upload_part_tasks = shared_upload_part_tasks

    @property
    def part_size(self) -> int:
        return self._part_size

    @property
    def max_retry_count(self) -> int:
        return self._max_retry_count

    @property
    def shared_prefetch_tasks(self) -> int:
        return self._shared_prefetch_tasks

    @property
    def shared_upload_part_tasks(self) -> int:
        return self._shared_upload_part_tasks


class TosClient(object):
    def __init__(self, region: str, endpoint: str = '', cred: Optional[CredentialProvider] = None,
                 client_conf: Optional[TosClientConfig] = None, use_native_client: bool = True,
                 enable_crc: bool = True):
        self._region = region
        self._endpoint = endpoint
        self._cred = CredentialProvider('', '') if cred is None else cred
        self._client_conf = TosClientConfig() if client_conf is None else client_conf
        self._part_size = self._client_conf.part_size
        self._use_native_client = use_native_client
        self._inner_client = None
        self._client_pid = None
        self._enable_crc = enable_crc

    def is_fork(self) -> bool:
        return multiprocessing.get_start_method() == 'fork'

    @property
    def _client(self) -> Any:
        if self._client_pid is None or self._client_pid != os.getpid() or self._inner_client is None:
            with _client_lock:
                if self._client_pid is None or self._client_pid != os.getpid() or self._inner_client is None:
                    if self._use_native_client:
                        if self._inner_client is not None:
                            if hasattr(self._inner_client, 'close') and callable(self._inner_client.close):
                                self._inner_client.close()
                        self._inner_client = tosnativeclient.TosClient(self._region, self._endpoint, self._cred.ak,
                                                                       self._cred.sk,
                                                                       self._client_conf.part_size,
                                                                       self._client_conf.max_retry_count,
                                                                       shared_prefetch_tasks=self._client_conf.shared_prefetch_tasks,
                                                                       enable_crc=self._enable_crc,
                                                                       shared_upload_part_tasks=self._client_conf.shared_upload_part_tasks,
                                                                       dns_cache_async_refresh=False)
                    else:
                        self._inner_client = tos.TosClientV2(self._cred.ak, self._cred.sk, endpoint=self._endpoint,
                                                             region=self._region,
                                                             max_retry_count=self._client_conf.max_retry_count,
                                                             enable_crc=self._enable_crc)
                    self._client_pid = os.getpid()
                    _client_map.add(self)

        assert self._inner_client is not None
        return self._inner_client

    @property
    def use_native_client(self) -> bool:
        return self._use_native_client

    def close(self):
        if isinstance(self._client, tosnativeclient.TosClient):
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

    def batch_get_objects(self, object_metas: List[Tuple[str, str, Optional[str], Optional[int], Optional[int]]],
                          reader_type: Optional[ReaderType] = None,
                          buffer_size: Optional[int] = None, prefetch_concurrency: int = 0,
                          fetch_etag_size: bool = False) -> List[
        TosObjectReader]:
        if isinstance(self._client, tosnativeclient.TosClient):
            native_object_streams = self._client.batch_get_objects(object_metas, prefetch_concurrency, fetch_etag_size)
            assert len(native_object_streams) == len(object_metas)
            return list(self._trans_to_object_readers(native_object_streams, reader_type=reader_type,
                                                      buffer_size=buffer_size))

        raise NotImplementedError()

    def _trans_to_object_readers(self, native_object_streams: Iterator[ReadStream],
                                 reader_type: Optional[ReaderType] = None,
                                 buffer_size: Optional[int] = None) -> Iterator[TosObjectReader]:

        for native_object_stream in native_object_streams:
            bucket, key, size, etag, crc64, fetch_etag_size_err = (native_object_stream.bucket,
                                                                   native_object_stream.key,
                                                                   native_object_stream.size(),
                                                                   native_object_stream.etag(),
                                                                   native_object_stream.crc64(),
                                                                   native_object_stream.fetch_etag_size_err())
            if size is None or etag is None or size == -1:
                get_object_meta = partial(self.head_object, bucket, key)
            else:
                get_object_meta = lambda: TosObjectMeta(bucket, key, size, etag, crc64)
            object_stream = _TosObjectStream(bucket, key, get_object_meta, False, self._client)
            if reader_type is not None and reader_type == ReaderType.RANGED:
                object_stream._random_object_stream = native_object_stream
                object_reader = RangedTosObjectReader(bucket, key, object_stream, buffer_size, fetch_etag_size_err)
            elif reader_type is not None and reader_type == ReaderType.DIRECT:
                object_stream._random_object_stream = native_object_stream
                object_reader = DirectTosObjectReader(bucket, key, object_stream, fetch_etag_size_err)
            else:
                object_stream._sequential_object_stream = native_object_stream
                object_reader = SequentialTosObjectReader(bucket, key, object_stream, fetch_etag_size_err)
            yield object_reader

    def get_object(self, bucket: str, key: str, etag: Optional[str] = None,
                   size: Optional[int] = None, reader_type: Optional[ReaderType] = None,
                   buffer_size: Optional[int] = None, preload: bool = False,
                   crc64: Optional[int] = None) -> TosObjectReader:
        log.debug(f'get_object tos://{bucket}/{key}')

        if size is None or etag is None or size == -1:
            get_object_meta = partial(self.head_object, bucket, key)
        else:
            get_object_meta = lambda: TosObjectMeta(bucket, key, size, etag, crc64)
        object_stream = _TosObjectStream(bucket, key, get_object_meta, preload, self._client)
        if reader_type is not None:
            if reader_type == ReaderType.RANGED:
                return RangedTosObjectReader(bucket, key, object_stream, buffer_size)
            if reader_type == ReaderType.DIRECT:
                return DirectTosObjectReader(bucket, key, object_stream)

        return SequentialTosObjectReader(bucket, key, object_stream)

    def put_object(self, bucket: str, key: str, storage_class: Optional[str] = None) -> TosObjectWriter:
        log.debug(f'put_object tos://{bucket}/{key}')

        if isinstance(self._client, tosnativeclient.TosClient):
            put_object_stream = self._client.put_object(bucket, key, storage_class=storage_class)
        else:
            put_object_stream = PutObjectStream(
                lambda content: self._client.put_object(bucket, key, storage_class=storage_class, content=content))

        return TosObjectWriter(bucket, key, put_object_stream)

    def head_object(self, bucket: str, key: str) -> TosObjectMeta:
        log.debug(f'head_object tos://{bucket}/{key}')

        if isinstance(self._client, tosnativeclient.TosClient):
            resp = self._client.head_object(bucket, key)
            return TosObjectMeta(resp.bucket, resp.key, resp.size, resp.etag, resp.crc64)

        resp = self._client.head_object(bucket, key)
        crc64 = None
        if resp.hash_crc64_ecma:
            crc64 = int(resp.hash_crc64_ecma)
        return TosObjectMeta(bucket, key, resp.content_length, resp.etag, crc64)

    def gen_list_stream(self, bucket: str, prefix: str, max_keys: int = 1000,
                        delimiter: Optional[str] = None,
                        continuation_token: Optional[str] = None,
                        list_background_buffer_count: int = 1,
                        prefetch_concurrency: int = 0,
                        distributed_info: Optional[Tuple[int, int, int, int]] = None) -> tosnativeclient.ListStream:
        log.debug(f'gen_list_stream tos://{bucket}/{prefix}')

        if isinstance(self._client, tosnativeclient.TosClient):
            delimiter = delimiter if delimiter is not None else ''
            continuation_token = continuation_token if continuation_token is not None else ''
            return self._client.list_objects(bucket, prefix, max_keys=max_keys, delimiter=delimiter,
                                             continuation_token=continuation_token,
                                             list_background_buffer_count=list_background_buffer_count,
                                             prefetch_concurrency=prefetch_concurrency,
                                             distributed_info=distributed_info)
        raise NotImplementedError()

    def list_objects(self, bucket: str, prefix: str, max_keys: int = 1000,
                     continuation_token: Optional[str] = None, delimiter: Optional[str] = None) -> Tuple[
        List[TosObjectMeta], bool, Optional[str]]:
        log.debug(f'list_objects tos://{bucket}/{prefix}')

        if isinstance(self._client, tosnativeclient.TosClient):
            raise NotImplementedError()

        resp = self._client.list_objects_type2(bucket, prefix, max_keys=max_keys, continuation_token=continuation_token,
                                               delimiter=delimiter)
        object_metas = []
        for obj in resp.contents:
            crc64 = None
            if obj.hash_crc64_ecma:
                crc64 = int(obj.hash_crc64_ecma)
            object_metas.append(TosObjectMeta(bucket, obj.key, obj.size, obj.etag, crc64))
        return object_metas, resp.is_truncated, resp.next_continuation_token


try:
    import bytedtos


    class TosCloudClient(object):
        def __init__(self, bucket, access_key, **kwargs):
            self.bucket = bucket
            self.access_key = access_key
            self._client_pid = None
            self._inner_client: Optional[bytedtos.Client] = None
            self._kwargs = dict(kwargs)

        @property
        def client(self) -> bytedtos.Client:
            if self._client_pid is None or self._client_pid != os.getpid() or self._inner_client is None:
                with _client_lock:
                    if self._client_pid is None or self._client_pid != os.getpid() or self._inner_client is None:
                        self._inner_client = bytedtos.Client(self.bucket, self.access_key, **self._kwargs)
                        self._client_pid = os.getpid()
                        _client_map.add(self)
            assert self._inner_client is not None
            return self._inner_client
except ImportError:
    pass
