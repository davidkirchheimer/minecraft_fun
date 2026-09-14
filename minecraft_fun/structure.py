"""Backend-agnostic structure model."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from .blocks import Block

Vec3 = tuple[int, int, int]


@dataclass(frozen=True)
class Box:
    """An inclusive axis-aligned box."""

    lo: Vec3
    hi: Vec3

    @property
    def size(self) -> Vec3:
        return tuple(hi - lo + 1 for lo, hi in zip(self.lo, self.hi, strict=True))  # type: ignore[return-value]

    @property
    def volume(self) -> int:
        x, y, z = self.size
        return x * y * z

    def __contains__(self, pos: Vec3) -> bool:
        return all(lo <= p <= hi for lo, p, hi in zip(self.lo, pos, self.hi, strict=True))

    def __iter__(self) -> Iterator[Vec3]:
        for x in range(self.lo[0], self.hi[0] + 1):
            for y in range(self.lo[1], self.hi[1] + 1):
                for z in range(self.lo[2], self.hi[2] + 1):
                    yield (x, y, z)


@dataclass
class Structure:
    """A sparse set of blocks at local coordinates, with (0, 0, 0) as the anchor.

    Positions absent from the structure are left untouched when it is placed;
    use an explicit air block to carve space out.
    """

    blocks: dict[Vec3, Block] = field(default_factory=dict)
    name: str = "structure"

    def __len__(self) -> int:
        return len(self.blocks)

    def __iter__(self) -> Iterator[tuple[Vec3, Block]]:
        return iter(self.blocks.items())

    def set(self, pos: Vec3, block: Block) -> Structure:
        self.blocks[pos] = block
        return self

    def get(self, pos: Vec3) -> Block | None:
        return self.blocks.get(pos)

    def fill(self, lo: Vec3, hi: Vec3, block: Block, hollow: bool = False) -> Structure:
        box = Box(
            tuple(min(a, b) for a, b in zip(lo, hi, strict=True)),  # type: ignore[arg-type]
            tuple(max(a, b) for a, b in zip(lo, hi, strict=True)),  # type: ignore[arg-type]
        )
        for pos in box:
            if hollow and not _on_shell(pos, box):
                continue
            self.blocks[pos] = block
        return self

    @property
    def bounds(self) -> Box:
        if not self.blocks:
            return Box((0, 0, 0), (0, 0, 0))
        xs, ys, zs = zip(*self.blocks, strict=True)
        return Box((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))

    def translated(self, offset: Vec3) -> Structure:
        dx, dy, dz = offset
        moved = {(x + dx, y + dy, z + dz): b for (x, y, z), b in self.blocks.items()}
        return Structure(moved, self.name)

    def rotated_y(self, quarter_turns: int) -> Structure:
        """Rotate clockwise about the Y axis through the anchor."""
        turns = quarter_turns % 4
        out: dict[Vec3, Block] = {}
        for (x, y, z), block in self.blocks.items():
            for _ in range(turns):
                x, z = -z, x
            out[(x, y, z)] = block.rotated_y(turns)
        return Structure(out, self.name)

    def mirrored(self, axis: str) -> Structure:
        if axis not in ("x", "z"):
            raise ValueError("axis must be 'x' or 'z'")
        out: dict[Vec3, Block] = {}
        for (x, y, z), block in self.blocks.items():
            pos = (-x, y, z) if axis == "x" else (x, y, -z)
            out[pos] = block.mirrored(axis)
        return Structure(out, self.name)

    def merged(self, other: Structure, offset: Vec3 = (0, 0, 0)) -> Structure:
        out = dict(self.blocks)
        out.update(other.translated(offset).blocks)
        return Structure(out, self.name)


def _on_shell(pos: Vec3, box: Box) -> bool:
    return any(p in (lo, hi) for p, lo, hi in zip(pos, box.lo, box.hi, strict=True))


def structure_from_blocks(
    blocks: Iterable[tuple[Vec3, Block]], name: str = "structure"
) -> Structure:
    return Structure(dict(blocks), name)
