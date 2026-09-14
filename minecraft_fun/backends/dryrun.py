"""An in-memory backend: lets generators be developed and tested without Minecraft."""

from __future__ import annotations

from ..blocks import Block
from ..structure import Box, Vec3
from .base import WorldBackend


class DryRunBackend(WorldBackend):
    """Records placements in a dict and can render horizontal slices as ASCII."""

    readable = True

    def __init__(self) -> None:
        self.world: dict[Vec3, Block] = {}
        self.writes = 0

    def place_block(self, pos: Vec3, block: Block) -> None:
        self.world[pos] = block
        self.writes += 1

    def get_block(self, pos: Vec3) -> Block | None:
        return self.world.get(pos)

    @property
    def bounds(self) -> Box:
        if not self.world:
            return Box((0, 0, 0), (0, 0, 0))
        xs, ys, zs = zip(*self.world, strict=True)
        return Box((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))

    def render_slice(self, y: int, legend: bool = True) -> str:
        """Render the XZ plane at height ``y``, one character per block id."""
        box = self.bounds
        symbols: dict[str, str] = {}
        alphabet = "#*+=%@&$0123456789abcdefghijklmnopqrstuvwxyz"
        rows = []
        for z in range(box.lo[2], box.hi[2] + 1):
            row = []
            for x in range(box.lo[0], box.hi[0] + 1):
                block = self.world.get((x, y, z))
                if block is None or block.id == "minecraft:air":
                    row.append(".")
                    continue
                short = block.id.split(":", 1)[1]
                if short not in symbols:
                    symbols[short] = alphabet[len(symbols) % len(alphabet)]
                row.append(symbols[short])
            rows.append("".join(row))
        out = "\n".join(rows)
        if legend and symbols:
            out += "\n" + "  ".join(f"{sym}={name}" for name, sym in symbols.items())
        return out
