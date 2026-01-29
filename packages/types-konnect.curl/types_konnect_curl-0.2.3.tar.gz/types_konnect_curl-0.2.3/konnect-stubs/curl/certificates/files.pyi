from .encodings import Encoding as Encoding
from _typeshed import Incomplete
from pathlib import Path
from typing import Final, Generic, TypeVar

T = TypeVar('T', bound=Encoding, covariant=True)
C = TypeVar('C', bound=Encoding)
DEFAULT_MAX_READ: Final[Incomplete]

class EncodedFile(Generic[T]):
    contents: Incomplete
    path: Incomplete
    def __init__(self, contents: T, path: Path) -> None: ...
    @classmethod
    def read(cls, path: Path, encoding: type[C], /, maxsize: int = ...) -> EncodedFile[C]: ...
    @staticmethod
    def write(path: Path, contents: C, /, *, exists_ok: bool = False) -> EncodedFile[C]: ...
