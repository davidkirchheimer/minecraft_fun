"""The interface every world backend implements."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..blocks import Block
from ..structure import Structure, Vec3


class WorldBackend(ABC):
    """A target that structures can be written to.

    Backends buffer writes where the transport benefits from it; callers must
    call :meth:`flush` (or use the context manager) to guarantee delivery.
    """

    readable: bool = False

    @abstractmethod
    def place_block(self, pos: Vec3, block: Block) -> None: ...

    def get_block(self, pos: Vec3) -> Block | None:
        raise NotImplementedError(f"{type(self).__name__} cannot read the world")

    def place_structure(self, structure: Structure, at: Vec3 = (0, 0, 0)) -> int:
        count = 0
        for pos, block in structure.translated(at):
            self.place_block(pos, block)
            count += 1
        return count

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.flush()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
