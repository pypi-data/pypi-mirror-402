import os
import io
from typing import List, Union, Optional, Generator
import dataclasses
from abc import ABC, abstractmethod
import urllib.parse
from contextlib import contextmanager
import logging
from pathlib import Path
from torch.distributed.checkpoint.filesystem import (
    FileSystemReader,
    FileSystemWriter,
    FileSystemBase
)
import bytedtos
from .tos_client import TosCloudClient
from torch.distributed.checkpoint.planner import SavePlan
from .tos_common import parse_tos_url, path_or_str_to_str
from toscloud_stream import TosCloudObjectReader, TosCloudObjectWriter, TosCloudSyncPutSteam, TosCloudSyncGetStream

logger = logging.getLogger(__name__)


class PrefixStrategyBase(ABC):
    """Base class for prefix generation strategies."""

    def __init__(self):
        pass

    def __call__(self, rank: int) -> str:
        """Generate prefix for given rank."""
        return self.generate_prefix(rank)

    @abstractmethod
    def generate_prefix(self, rank: int) -> str:
        """Generate storage prefix for the given rank."""
        pass


class DefaultPrefixStrategy(PrefixStrategyBase):
    """Default strategy for generating  prefixes."""

    def generate_prefix(self, rank: int) -> str:
        """Generate simple rank-based name without prefix."""
        return f"__{rank}_"


class StorageMetadata:
    """Metadata for storage prefix."""

    def __init__(self, prefix: str):
        self.prefix = prefix


class TOSFileSystem(FileSystemBase):
    """
    TOS (Tencent Object Storage) 文件系统实现，兼容 PyTorch 分布式检查点接口。
    
    实现 FileSystemBase 抽象基类的所有方法，提供与 TOS 交互的功能。
    """

    def __init__(self, region: str, endpoint: str,
                 access_key: str = "", secret_key: str = ""):
        """
        初始化 TOS 文件系统客户端。
        
        Args:
            region: TOS 区域
            endpoint: TOS 端点 URL
            access_key_id: 访问密钥 ID（可选，如不提供将尝试从环境变量读取）
            secret_access_key: 秘密访问密钥（可选，如不提供将尝试从环境变量读取）
        """
        self.cli_wrapper = TosCloudClient(bucket='dataset-test-why', access_key=access_key, secret_key=secret_key,
                                          endpoint=endpoint, region=region)

    @contextmanager
    def create_stream(self, path: Union[str, os.PathLike], mode: str) -> Generator[io.IOBase, None, None]:
        """
        创建一个文件流用于读写操作。
        
        Args:
            path: 文件路径，格式为 "bucket/key"
            mode: 文件模式，'r' 表示读取，'w' 表示写入
            
        Yields:
            一个 IOBase 对象，用于文件读写
        """
        path_str = path_or_str_to_str(path)
        bucket, key = parse_tos_url(path_str)
        print(f"create stream: path: {path_str} mode: {mode}")

        if mode == 'rb':
            # 读取模式：获取对象内容并创建 BytesIO 流
            with TosCloudObjectReader(bucket=bucket, key=key,
                                      stream=TosCloudSyncGetStream(self.cli_wrapper.client, key)) as stream:
                yield stream
        elif mode == 'wb':
            with TosCloudObjectWriter(bucket=bucket, key=key,
                                      put_stream=TosCloudSyncPutSteam(self.cli_wrapper.client, key)) as stream:
                yield stream
            # 写入模式：创建 BytesIO 流，在上下文退出时上传内容
        else:
            raise ValueError(f"Unsupported mode: {mode}. Only 'rb' and 'wb' are supported.")

    def concat_path(self, path: Union[str, os.PathLike], suffix: str) -> Union[str, os.PathLike]:
        """
        连接路径和后缀。
        
        Args:
            path: 基础路径
            suffix: 要添加的后缀
            
        Returns:
            连接后的路径
        """
        logger.debug("concat paths %s and %s", path, suffix)
        path_str = os.fspath(path)
        result = os.path.join(path_str, suffix)
        return result

    def rename(self, old_path: Union[str, os.PathLike], new_path: Union[str, os.PathLike]) -> None:
        """
        重命名（移动）对象。
        
        Args:
            path: 源路径
            new_path: 目标路径
        """
        logger.debug("rename %s to %s", old_path, new_path)

        old_path_str = path_or_str_to_str(old_path)
        new_path_str = path_or_str_to_str(new_path)

        old_bucket, old_key = parse_tos_url(old_path_str)
        escaped_old_key = self._escape_path(old_key)
        logger.debug("rename: escaped version of the source key: %s", escaped_old_key)
        new_bucket, new_key = parse_tos_url(new_path_str)

        if old_bucket != new_bucket:
            raise ValueError(
                f"Source and destination buckets cannot be different (rename does not support cross-buckets operations)"
            )
        print(f"rename: source key: {old_path_str} dst key: {new_path_str}")
        try:
            # 复制对象
            self.cli_wrapper.client.copy_object(
                src_object=old_key,
                dst_object=new_key
            )
            # 删除源对象
            self.cli_wrapper.client.delete_object(key=old_key)

        except bytedtos.TosException as e:
            raise IOError(f"Failed to rename object: {e}")

    def init_path(self, path: Union[str, os.PathLike]) -> Union[str, os.PathLike]:
        """
        初始化路径。在 TOS 中，这主要是验证路径格式。
        
        Args:
            path: 要初始化的路径
            
        Returns:
            初始化后的路径
        """
        logger.debug("init_path for %s", path)
        self._path = path
        return self._path

    def mkdir(self, path: Union[str, os.PathLike]) -> None:
        """
        创建目录。在 TOS 中，这通常意味着创建一个空对象作为目录标记。
        
        Args:
            path: 要创建的目录路径
        """
        pass

    @classmethod
    def validate_checkpoint_id(cls, checkpoint_id: Union[str, os.PathLike]) -> bool:
        """
        验证检查点 ID 是否有效。
        
        Args:
            checkpoint_id: 要验证的检查点 ID
            
        Returns:
            如果检查点 ID 有效，则为 True，否则为 False
        """
        logger.debug("validate_checkpoint_id for %s", checkpoint_id)

        if isinstance(checkpoint_id, Path):
            return True

        try:
            parse_tos_url(path_or_str_to_str(checkpoint_id))
        except ValueError:
            return False
        return True

    def exists(self, path: Union[str, os.PathLike]) -> bool:
        """
        检查路径是否存在。
        
        Args:
            path: 要检查的路径
            
        Returns:
            如果路径存在，则为 True，否则为 False
        """
        logger.debug("exists %s", path)

        path_str = path_or_str_to_str(path)
        bucket, key = parse_tos_url(path_str)
        try:
            self.cli_wrapper.client.head_object(key=key)
        except bytedtos.TosException as e:
            if e.code != 404:
                raise
            return False
        return True

    def rm_file(self, path: Union[str, os.PathLike]) -> None:
        """
        删除文件。
        
        Args:
            path: 要删除的文件路径
        """
        logger.debug("remove %s", path)

        path_str = path_or_str_to_str(path)
        bucket, key = parse_tos_url(path_str)

        try:
            self.cli_wrapper.client.delete_object(key=key)
        except bytedtos.TosException as e:
            raise IOError(f"Failed to delete file: {e}")

    def _escape_path(sefl, string):
        """URL-encodes path segments while preserving '/' separators using urllib.parse.quote().

        Args:
            string (str): URL path string to escape

        Returns:
            str: Path string with each segment percent-encoded, separators preserved
        """
        if not string:
            return string
        parts = []
        for part in string.split("/"):
            parts.append(urllib.parse.quote(part, safe=""))
        return "/".join(parts)


class TosDistributedCkptWriter(FileSystemWriter):
    def __init__(self, path: str, region: str = "", endpoint: str = "", access_key: str = "", secret_key: str = "",
                 prefix_strategy: Optional[PrefixStrategyBase] = None, **kwargs):
        super().__init__(
            path=path,
            sync_files=False,
            **kwargs
        )
        self.bucket, self.prefix = parse_tos_url(path)
        self.region = region
        self.endpoint = endpoint
        self.prefix_strategy = prefix_strategy or DefaultPrefixStrategy()
        self.fs = TOSFileSystem(region=self.region, endpoint=self.endpoint, access_key=access_key,
                                secret_key=secret_key)

    def prepare_global_plan(self, plans: List[SavePlan]) -> List[SavePlan]:
        """
        Prepare save plans with specific storage metadata.

        Args:
            plans: List of save plans to be processed.

        Returns:
            Modified save plans with storage metadata.
        """
        return [
            dataclasses.replace(
                plan, storage_data=StorageMetadata(self.prefix_strategy(idx))
            )
            for idx, plan in enumerate(plans)
        ]

    def validate_checkpoint_id(self, checkpoint_id: Union[str, os.PathLike]) -> bool:
        return self.fs.validate_checkpoint_id(checkpoint_id)


class TosDistributedCkptReader(FileSystemReader):
    def __init__(self, path: str, region: str = "", endpoint: str = "", access_key: str = "", secret_key: str = "",
                 **kwargs):
        self.path = path
        self.region = region
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.fs = TOSFileSystem(region=self.region, endpoint=self.endpoint, access_key=self.access_key,
                                secret_key=self.secret_key)

    def validate_checkpoint_id(self, checkpoint_id: Union[str, os.PathLike]) -> bool:
        return self.fs.validate_checkpoint_id(checkpoint_id)
