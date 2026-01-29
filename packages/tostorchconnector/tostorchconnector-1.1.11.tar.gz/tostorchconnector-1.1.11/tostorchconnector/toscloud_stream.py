from ast import List
from http import client
from abc import ABC, abstractmethod
from os import SEEK_SET, SEEK_CUR, SEEK_END
import io
import threading
import bytedtos
import logging
from typing import Union, Optional

from urllib3 import Retry
from run_execption import StreamWriteExecption, StreamReadExecption

from tostorchconnector import tos_client

logger = logging.getLogger(__name__)

# 防止part太多了 10MB，当前内场tos不支持最后一个part小于5MB，所以需要缓存至少2个part到内存里
DEFAULT_PART_SIZE = 10 * 1024 * 1024


class TosCloudSyncPutSteam(object):
    def __init__(self, client: bytedtos.Client, key: str, part_size=DEFAULT_PART_SIZE):
        self._client = client
        self._buffer = io.BytesIO()
        self._part_number = []
        self._part_idx = 1
        self.upload_id = ""
        self._key = key
        self._part_size = part_size

    def write(self, data: Union[bytes, memoryview]) -> int:
        # BytesIO 支持 buffer 协议，直接写入内存视图/字节
        self._buffer.write(data)
        self._write_offset += len(data)

        buf = self._buffer.getbuffer()  # memoryview，零拷贝视图
        nbytes = buf.nbytes
        # 触发阈值：缓冲累计达到至少两个分片
        if nbytes >= self._part_size * 2:
            # 首次分片需要初始化 upload_id
            if not self.upload_id:
                try:
                    # 初始化分片上传，兼容返回 upload_id 字段或直接返回字符串
                    resp = self._client.init_upload(key=self._key)
                    self.upload_id = resp.upload_id()
                except bytedtos.TosException as e:
                    logger.error(f'init_upload failed: {e}')
                    raise e

            nparts = nbytes // self._part_size
            assert nparts >= 2, 'nparts must be >= 2'
            # 为避免 close 阶段出现“尾部 < part_size”的错误，保留最后一个完整分片在缓冲区
            flush_end = (nparts - 1) * self._part_size
            try:
                # 单次upload_part：把 [0, flush_end) 作为一个分片上传
                chunk_view = buf[:flush_end]
                self._client.upload_part(
                    key=self._key,
                    upload_id=self.upload_id,
                    part_number=self._part_idx,
                    body=chunk_view,
                )
                self._part_number.append(self._part_idx)
                self._part_idx += 1
            except bytedtos.TosException as e:
                logger.error(f'upload_part failed: {e}')
                raise e

            # 剔除已上传的前缀，仅保留尾部（可能为完整一分片+不足一分片的余量）
            tail_view = buf[flush_end:]
            self._buffer = io.BytesIO()
            self._buffer.write(tail_view)
        return len(data)

    def close(self):
        if not self._closed:
            self._closed = True
            tail_data = self._buffer.getbuffer()
            try:
                if len(tail_data) == 0 and len(self._part_number) == 0:
                    return
                elif len(tail_data) > 0 and len(self._part_number) == 0:
                    self._client.put_object(
                        key=self._key,
                        data=tail_data
                    )
                elif len(self._part_number) > 0:
                    if len(tail_data) > 0 and len(tail_data) < self._part_size:
                        raise StreamWriteExecption(
                            f'Part size {len(tail_data)} is smaller than {self._part_size} when close')
                    if len(tail_data) > 0:
                        self._client.upload_part(
                            key=self._key,
                            upload_id=self.upload_id,
                            part_number=self._part_idx,
                            body=tail_data
                        )
                        self._part_idx += 1
                        self._part_number.append(self._part_idx)
                    self._client.complete_upload(
                        key=self._key,
                        upload_id=self.upload_id,
                        part_list=self._part_number
                    )
                else:
                    raise StreamWriteExecption(f'no match close mode')
            except (bytedtos.TosException, StreamWriteExecption) as e:
                logger.error(f'exception occurred when closing stream: {e}')
                raise e


class TosCloudObjectWriter(io.BufferedIOBase):
    def __init__(self, bucket: str, key: str, put_stream: TosCloudSyncPutSteam):
        if not bucket:
            raise ValueError('bucket is empty')
        self._bucket = bucket
        self._key = key
        self._client = client
        self._write_offset = 0
        self._lock = threading.Lock()
        self._put_object_stream = put_stream
        self._lock = threading.Lock()
        self._closed = False
        self._inited = False

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def key(self) -> str:
        return self._key

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def __enter__(self):
        with self._lock:
            if not self._inited:
                self._inited = True
                self._write_offset = 0
            else:
                raise StreamWriteExecption('double enter')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            try:
                logger.info(f'exception occurred before closing stream: {exc_type.__name__}: {exc_val}')
            except:
                pass
        else:
            self.close()

    def write(self, data: Union[bytes, memoryview]) -> int:
        with self._lock:
            if self._closed:
                raise StreamWriteExecption('write on closed stream')
            writed = self._put_object_stream.write(data)
            self._write_offset += writed
            return writed

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._closed = True
                self._put_object_stream.close()

    def tell(self) -> int:
        with self._lock:
            return self._write_offset

    def flush(self) -> None:
        pass

    def readable(self) -> bool:
        return False

    def writable(self) -> bool:
        with self._lock:
            return not self._closed

    def seekable(self) -> bool:
        return False


class TosCloudSyncGetStream(object):
    def __init__(self, client: bytedtos.Client, key: str):
        self._client = client
        self._key = key
        try:
            resp = self._client.head_object(key=self._key)
            self._size = resp.size()
        except bytedtos.TosException as e:
            logger.error(f'head_object failed: {e}')
            raise e

    def read(self, start: int, length: Optional[int] = None) -> bytes:
        if length == 0:
            return b''
        if length is None or length < 0:
            end = self._size - 1
        elif length > 0 and start + length - 1 < self._size:
            end = start + length - 1
        else:
            raise StreamReadExecption(f'length {length} is out of range [{start},{self._size - 1}]')
        try:
            resp = self._client.get_object_range(key=self._key, start=start, end=end)
            return resp.data
        except bytedtos.TosException as e:
            logger.error(f'get_object failed: {e}')
            raise e

    def close(self) -> None:
        pass


class TosCloudObjectReader(io.BufferedIOBase):
    def __init__(self, bucket: str, key: str, stream: TosCloudSyncGetStream):
        if not bucket:
            raise ValueError('bucket is empty')
        self._bucket = bucket
        self._key = key
        self._stream = stream
        self._read_offset = 0
        self._closed = False
        self._inited = False
        self._lock = threading.Lock()

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def key(self) -> str:
        return self._key

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._closed = True
                self._stream.close()

    def __enter__(self):
        with self._lock:
            if not self._inited:
                self._inited = True
                self._read_offset = 0
            else:
                raise StreamReadExecption('double enter')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            try:
                logger.info(f'exception occurred before closing stream: {exc_type.__name__}: {exc_val}')
            except:
                pass
        else:
            self.close()

    def read(self, size: Optional[int] = None) -> bytes:
        with self._lock:
            if self._closed:
                raise StreamReadExecption('read on closed stream')
            return self._stream.read(self._read_offset, size)

    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        with self._lock:
            if self._closed:
                raise StreamReadExecption('read on closed stream')
            if whence != SEEK_SET:
                raise StreamReadExecption(f'whence {whence} is not SEEK_SET')
            self._read_offset = offset
            return self._read_offset

    def tell(self) -> int:
        with self._lock:
            return self._read_offset

    def readable(self) -> bool:
        with self._lock:
            return not self._closed

    def writable(self) -> bool:
        return False

    def seekable(self) -> bool:
        return True
