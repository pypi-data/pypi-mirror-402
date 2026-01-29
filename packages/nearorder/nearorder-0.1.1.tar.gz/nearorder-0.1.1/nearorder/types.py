from typing import Callable, Literal, TypeVar, Protocol

T = TypeVar("T", covariant=True)

Order = Literal["asc", "desc"]
Cmp = Callable[[T, T], int]


class RandomAccess(Protocol[T]):
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> T: ...
