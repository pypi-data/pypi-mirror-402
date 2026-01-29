from typing import Optional

from tosnativeclient.tosnativeclient import ReadStream


class TosObjectMeta(object):
    def __init__(self, bucket: str, key: str, size: Optional[int] = None, etag: Optional[str] = None,
                 crc64: Optional[int] = None):
        self._bucket = bucket
        self._key = key
        self._size = size
        self._etag = etag
        self._crc64 = crc64
        self._native_object_stream: Optional[ReadStream] = None

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def key(self) -> str:
        return self._key

    @property
    def size(self) -> Optional[int]:
        return self._size

    @property
    def etag(self) -> Optional[str]:
        return self._etag

    @property
    def crc64(self) -> Optional[int]:
        return self._crc64
