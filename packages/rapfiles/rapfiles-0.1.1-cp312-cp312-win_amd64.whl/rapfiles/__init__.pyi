"""Type stubs for rapfiles public API."""

from typing import (
    Any,
    Optional,
    Union,
    List,
    Tuple,
)

from ._rapfiles import (
    FileMetadata,
)

__version__: str

# Convenience async functions
async def read_file(path: str) -> str: ...
async def write_file(path: str, contents: str) -> None: ...
async def read_file_bytes(path: str) -> bytes: ...
async def write_file_bytes(path: str, contents: bytes) -> None: ...
async def append_file(path: str, contents: str) -> None: ...

# Directory operations
async def create_dir(path: str) -> None: ...
async def create_dir_all(path: str) -> None: ...
async def remove_dir(path: str) -> None: ...
async def remove_dir_all(path: str) -> None: ...
async def list_dir(path: str) -> List[str]: ...
async def exists(path: str) -> bool: ...
async def is_file(path: str) -> bool: ...
async def is_dir(path: str) -> bool: ...

# Metadata operations
async def stat(path: str) -> FileMetadata: ...
async def metadata(path: str) -> FileMetadata: ...

# Directory traversal
async def walk_dir(path: str) -> List[Tuple[str, bool]]: ...

# File opening - returns an async context manager
def open(
    file: Union[str, bytes],
    mode: str = ...,
    buffering: int = ...,
    encoding: Optional[str] = ...,
    errors: Optional[str] = ...,
    newline: Optional[str] = ...,
    closefd: bool = ...,
    opener: Optional[Any] = ...,
) -> Any: ...  # Returns _OpenContextManager which is internal

# Re-export types
__all__: List[str]
