import io
import logging
import threading
from abc import ABC, abstractmethod
from functools import partial, cached_property
from os import SEEK_SET, SEEK_CUR, SEEK_END
from typing import Optional, Callable, Any

import tosnativeclient
from .tos_object_meta import TosObjectMeta

log = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1 * 1024 * 1024
DEFAULT_BUFFER_SIZE = 8 * 1024 * 1024


class _TosObjectStream(object):
    def __init__(self, bucket: str, key: str, get_object_meta: Optional[Callable[[], TosObjectMeta]],
                 preload: bool, client: Any):
        self._bucket = bucket
        self._key = key
        self._get_object_meta = get_object_meta
        self._preload = preload
        self._client = client
        self._sequential_object_stream = None
        self._sequential_object_stream_offset = 0
        self._random_object_stream = None

    def sequential_read(self, chunk_size) -> Optional[bytes]:
        self._trigger_prefetch()
        if chunk_size <= 0:
            chunk_size = DEFAULT_CHUNK_SIZE
        if isinstance(self._sequential_object_stream, tosnativeclient.ReadStream):
            chunk = self._sequential_object_stream.read(self._sequential_object_stream_offset, chunk_size)
            if chunk:
                self._sequential_object_stream_offset += len(chunk)
        else:
            chunk = self._sequential_object_stream.read(chunk_size)
        return chunk

    def random_read(self, read_start, read_end, chunk_size, callback: Callable[[bytes], None]) -> None:
        if chunk_size <= 0:
            chunk_size = DEFAULT_CHUNK_SIZE
        if isinstance(self._client, tosnativeclient.TosClient):
            if self._random_object_stream is None:
                object_meta = self.object_meta
                self._random_object_stream = self._client.get_object(self._bucket, self._key, object_meta.etag,
                                                                     object_meta.size, object_meta.crc64, self._preload)

            offset = read_start
            while 1:
                if offset >= read_end:
                    break
                length = chunk_size if offset + chunk_size <= read_end else read_end - offset
                chunk = self._random_object_stream.read(offset, length)
                if not chunk:
                    break
                callback(chunk)
                offset += len(chunk)
            return

        object_meta = self.object_meta
        output = self._client.get_object(self._bucket, self._key, if_match=object_meta.etag,
                                         range=f'bytes={read_start}-{read_end - read_start - 1}')
        while 1:
            chunk = output.read(chunk_size)
            if not chunk:
                break
            callback(chunk)

    def _trigger_prefetch(self) -> None:
        if self._sequential_object_stream is None:
            object_meta = self.object_meta
            if isinstance(self._client, tosnativeclient.TosClient):
                get_object_stream = partial(self._client.get_object, self._bucket, self._key)
            else:
                get_object_stream = lambda et, sz, c, p: self._client.get_object(self._bucket, self._key, '', et)
            self._sequential_object_stream = get_object_stream(object_meta.etag, object_meta.size, object_meta.crc64,
                                                               self._preload)

    @cached_property
    def object_meta(self) -> TosObjectMeta:
        return self._get_object_meta()

    def close(self) -> None:
        if self._sequential_object_stream and isinstance(self._sequential_object_stream, tosnativeclient.ReadStream):
            try:
                self._sequential_object_stream.close()
            except Exception as ex:
                log.warning(f'failed to close sequential object stream: {ex}')
        if self._random_object_stream and isinstance(self._random_object_stream, tosnativeclient.ReadStream):
            try:
                self._random_object_stream.close()
            except Exception as ex:
                log.warning(f'failed to close random object stream: {ex}')


class TosObjectReader(ABC, io.BufferedIOBase):
    def __init__(self, bucket: str, key: str, object_stream: _TosObjectStream,
                 fetch_etag_size_err: Optional[str] = None):
        if not bucket:
            raise ValueError('bucket is empty')
        self._bucket = bucket
        self._key = key
        self._object_stream = object_stream
        self._fetch_etag_size_err = fetch_etag_size_err
        self._total_size: Optional[int] = None
        self._read_offset = 0
        self._closed = False
        self._lock = threading.Lock()

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def key(self) -> str:
        return self._key

    @property
    def size(self) -> Optional[int]:
        return self._object_stream.object_meta.size

    @property
    def etag(self) -> Optional[str]:
        return self._object_stream.object_meta.etag

    @property
    def crc64(self) -> Optional[int]:
        return self._object_stream.object_meta.crc64

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        if self._closed:
            return
        with self._lock:
            if not self._closed:
                self._closed = True
                if self._object_stream:
                    self._object_stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            try:
                log.info(f'exception occurred before closing stream: {exc_type.__name__}: {exc_val}')
            except:
                pass
            finally:
                self.close()
        else:
            self.close()

    def read(self, size: Optional[int] = None) -> bytes:
        if size is not None and not isinstance(size, int):
            raise TypeError(f"argument should be integer or None, not {type(size)!r}")
        if self._fetch_etag_size_err is not None:
            raise RuntimeError(self._fetch_etag_size_err)

        if self._is_read_to_end():
            return b''

        if self.closed:
            raise RuntimeError('read on closed TosObjectReader')
        return self._do_read(size)

    def readinto(self, buf) -> int:
        if self._fetch_etag_size_err is not None:
            raise RuntimeError(self._fetch_etag_size_err)
        size = len(buf)
        if self._is_read_to_end() or size == 0:
            return 0

        if self.closed:
            raise RuntimeError('read on closed TosObjectReader')
        return self._do_readinto(buf)

    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        if self._fetch_etag_size_err is not None:
            raise RuntimeError(self._fetch_etag_size_err)
        if whence == SEEK_END:
            if offset >= 0:
                self._read_offset = self._get_total_size()
                return self._read_offset
            # offset is negative
            offset += self._get_total_size()
        elif whence == SEEK_CUR:
            if offset >= 0 and self._is_read_to_end():
                return self._read_offset
            offset += self._read_offset
        elif whence == SEEK_SET:
            pass
        else:
            raise ValueError('invalid whence, must be passed SEEK_CUR, SEEK_SET, or SEEK_END')

        if offset < 0:
            raise ValueError(f'invalid seek offset {offset}')

        return self._do_seek(offset)

    @abstractmethod
    def _do_read(self, size: Optional[int] = None) -> bytes:
        pass

    @abstractmethod
    def _do_readinto(self, buf) -> int:
        pass

    @abstractmethod
    def _do_seek(self, offset: int) -> int:
        pass

    def tell(self) -> int:
        return self._read_offset

    def readable(self) -> bool:
        return not self.closed

    def writable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return not self.closed

    def _is_read_to_end(self) -> bool:
        return self._read_offset == self._get_total_size()

    def _get_total_size(self) -> int:
        if self._total_size is None:
            self._total_size = self._object_stream.object_meta.size
        return self._total_size


class DirectTosObjectReader(TosObjectReader):
    def __init__(self, bucket: str, key: str, object_stream: _TosObjectStream,
                 fetch_etag_size_err: Optional[str] = None):
        super().__init__(bucket, key, object_stream, fetch_etag_size_err)

    def _do_read(self, size: Optional[int] = None) -> bytes:
        read_start = self._read_offset

        if size is None or size < 0:
            # means read all
            read_end = self._get_total_size()
        else:
            read_end = min(read_start + size, self._get_total_size())

        buffer = io.BytesIO()

        def callback(data: bytes):
            nonlocal buffer
            buffer.write(data)

        self._object_stream.random_read(read_start, read_end, DEFAULT_CHUNK_SIZE, callback)
        self._read_offset += buffer.tell()
        return buffer.getvalue()

    def _do_readinto(self, buf) -> int:
        try:
            view = memoryview(buf)
            if view.readonly:
                raise TypeError(f'argument must be a writable bytes-like object, not {type(buf).__name__}')
        except TypeError:
            raise TypeError(f'argument must be a writable bytes-like object, not {type(buf).__name__}')

        read_start = self._read_offset
        read_end = min(read_start + len(buf), self._get_total_size())
        if read_start >= read_end:
            return 0

        readed = 0

        def callback(data: bytes):
            nonlocal readed
            nonlocal view
            view[readed: readed + len(data)] = data
            readed += len(data)

        self._object_stream.random_read(read_start, read_end, DEFAULT_CHUNK_SIZE, callback)
        self._read_offset += readed
        return readed

    def _do_seek(self, offset: int) -> int:
        self._read_offset = offset
        return self._read_offset


class SequentialTosObjectReader(TosObjectReader):

    def __init__(self, bucket: str, key: str, object_stream: _TosObjectStream,
                 fetch_etag_size_err: Optional[str] = None):
        super().__init__(bucket, key, object_stream, fetch_etag_size_err)
        self._buffer = io.BytesIO()

    def _do_read(self, size: Optional[int] = None) -> bytes:
        current_read_offset = self._read_offset
        if size is None or size < 0:
            # means read all
            self._buffer.seek(0, SEEK_END)
            while 1:
                chunk = self._object_stream.sequential_read(DEFAULT_CHUNK_SIZE)
                if not chunk:
                    break
                self._buffer.write(chunk)
        else:
            self.seek(size, SEEK_CUR)

        self._buffer.seek(current_read_offset)
        data = self._buffer.read(size)
        self._read_offset = self._buffer.tell()
        return data

    def _do_readinto(self, buf) -> int:
        current_read_offset = self._read_offset
        self.seek(len(buf), SEEK_CUR)
        self._buffer.seek(current_read_offset)
        readed = self._buffer.readinto(buf)
        self._read_offset = self._buffer.tell()
        return readed

    def _do_seek(self, offset: int) -> int:
        if offset > self._buffer_size():
            self._prefetch_to_offset(offset)

        offset = min(offset, self._get_total_size())
        self._read_offset = self._buffer.seek(offset)
        return self._read_offset

    def _prefetch_to_offset(self, offset: int) -> None:
        if self.closed:
            raise RuntimeError('read on closed TosObjectReader')
        size = self._buffer.seek(0, SEEK_END)
        while offset > size:
            chunk = self._object_stream.sequential_read(DEFAULT_CHUNK_SIZE)
            if not chunk:
                break
            size += self._buffer.write(chunk)

    def _buffer_size(self) -> int:
        cur_pos = self._buffer.tell()
        self._buffer.seek(0, SEEK_END)
        buffer_size = self._buffer.tell()
        self._buffer.seek(cur_pos)
        return buffer_size


class RangedTosObjectReader(TosObjectReader):
    def __init__(self, bucket: str, key: str,
                 object_stream: _TosObjectStream, buffer_size: Optional[int] = None,
                 fetch_etag_size_err: Optional[str] = None):
        super().__init__(bucket, key, object_stream, fetch_etag_size_err)

        if buffer_size is None:
            self._buffer_size = DEFAULT_BUFFER_SIZE
            self._enable_buffering = True
        else:
            self._buffer_size = buffer_size
            self._enable_buffering = buffer_size > 0

        self._buffer = bytearray(self._buffer_size) if self._enable_buffering else None
        self._buffer_view = memoryview(self._buffer) if self._buffer else None
        self._buffer_start = 0
        self._buffer_end = 0

    def _do_read(self, size: Optional[int] = None) -> bytes:
        read_start = self._read_offset
        if size is None or size < 0:
            read_end = self._get_total_size()
        else:
            read_end = min(read_start + size, self._get_total_size())

        if read_start >= read_end:
            return b''

        view = memoryview(bytearray(read_end - read_start))
        self._read_into_view(view, read_start, read_end)
        return view.tobytes()

    def _do_readinto(self, buf) -> int:
        try:
            view = memoryview(buf)
            if view.readonly:
                raise TypeError(f'argument must be a writable bytes-like object, not {type(buf).__name__}')
        except TypeError:
            raise TypeError(f'argument must be a writable bytes-like object, not {type(buf).__name__}')

        read_start = self._read_offset
        read_end = min(read_start + len(buf), self._get_total_size())
        if read_start >= read_end:
            return 0

        return self._read_into_view(view, read_start, read_end)

    def _do_seek(self, offset: int) -> int:
        self._read_offset = min(offset, self._get_total_size())
        return self._read_offset

    def _read_into_view(self, view: memoryview, read_start: int, read_end: int) -> int:
        readed = 0
        if self._buffer_start <= read_start < self._buffer_end <= read_end:
            readed_once = self._read_from_buffer(view, read_start, self._buffer_end)
            read_start = self._buffer_end
            view = view[readed_once:]
            readed += readed_once

        if read_end - read_start >= self._buffer_size or not self._enable_buffering:
            readed += self._read_directly(view, read_start, read_end)
        else:
            readed += self._read_from_buffer(view, read_start, read_end)

        self._read_offset += readed
        return readed

    def _read_directly(self, view: memoryview, read_start: int, read_end: int) -> int:
        readed = 0

        def callback(data: bytes):
            nonlocal readed
            nonlocal view
            view[readed: readed + len(data)] = data
            readed += len(data)

        self._object_stream.random_read(read_start, read_end, DEFAULT_CHUNK_SIZE, callback)
        return readed

    def _read_from_buffer(self, view: memoryview, read_start: int, read_end: int) -> int:
        if read_start < self._buffer_start or read_end > self._buffer_end:
            self._load_buffer(read_start)

        buffer_offset = read_start - self._buffer_start
        readed = read_end - read_start
        assert self._buffer is not None
        view[:readed] = self._buffer[buffer_offset:buffer_offset + readed]
        return readed

    def _load_buffer(self, read_start: int) -> None:
        read_end = min(read_start + self._buffer_size, self._get_total_size())
        assert self._buffer_view is not None

        readed = 0

        def callback(data: bytes):
            nonlocal readed
            self._buffer_view[readed: readed + len(data)] = data
            readed += len(data)

        self._object_stream.random_read(read_start, read_end, DEFAULT_CHUNK_SIZE, callback)

        self._buffer_start = read_start
        self._buffer_end = read_start + readed
