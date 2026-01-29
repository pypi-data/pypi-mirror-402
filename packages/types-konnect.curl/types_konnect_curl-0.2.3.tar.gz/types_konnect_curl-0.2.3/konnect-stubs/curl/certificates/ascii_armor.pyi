from _typeshed import Incomplete
from collections.abc import Iterator, Sequence
from typing import Literal, Self, SupportsIndex, TypeAlias, overload

BytesType: TypeAlias = Sequence[SupportsIndex]
Header: TypeAlias = tuple[str, str]
CHR_EQL: Incomplete
CHR_DASH: Incomplete

class ArmoredData(bytes):
    def __new__(cls, label: str, source: BytesType, headers: Sequence[Header] | None = None) -> Self: ...
    label: Incomplete
    headers: Sequence[Header]
    def __init__(self, label: str, source: BytesType, headers: Sequence[Header] | None = None) -> None: ...
    def encode_lines(self) -> Iterator[bytes]: ...
    @overload
    @classmethod
    def extract(cls, data: bytes | bytearray, *, with_unarmored: Literal[True]) -> Iterator[Self | str]: ...
    @overload
    @classmethod
    def extract(cls, data: bytes | bytearray, *, with_unarmored: Literal[False] = False) -> Iterator[Self]: ...
