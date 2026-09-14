"""Live world edits against a vanilla/Paper server over RCON.

Requires ``enable-rcon=true``, ``rcon.port`` and ``rcon.password`` in
``server.properties``. Write-only: the RCON transport gives no way to read
blocks back, so :meth:`get_block` is unsupported.

Runs of identical blocks along the X axis are coalesced into ``/fill``
commands, which cuts the number of round-trips by an order of magnitude on
typical builds.
"""

from __future__ import annotations

import os

from ..blocks import Block
from ..structure import Vec3
from .base import WorldBackend

FILL_LIMIT = 32768


class RconBackend(WorldBackend):
    readable = False

    def __init__(
        self,
        host: str = "127.0.0.1",
        password: str | None = None,
        port: int = 25575,
        buffering: bool = True,
    ) -> None:
        try:
            from mcrcon import MCRcon
        except ImportError as exc:  # pragma: no cover - depends on extras
            raise ImportError(
                "RconBackend needs the 'rcon' extra: pip install 'minecraft-fun[rcon]'"
            ) from exc

        password = password if password is not None else os.environ.get("RCON_PASSWORD")
        if not password:
            raise ValueError("RCON password required (argument or RCON_PASSWORD env var)")

        self._conn = MCRcon(host, password, port=port)
        self._conn.connect()
        self._buffering = buffering
        self._buffer: dict[Vec3, Block] = {}

    def command(self, cmd: str) -> str:
        return self._conn.command(cmd)

    def place_block(self, pos: Vec3, block: Block) -> None:
        if self._buffering:
            self._buffer[pos] = block
            return
        x, y, z = pos
        self.command(f"setblock {x} {y} {z} {block}")

    def forceload(self, lo: Vec3, hi: Vec3) -> None:
        """Keep the target chunks loaded; edits to unloaded chunks are dropped."""
        self.command(f"forceload add {lo[0]} {lo[2]} {hi[0]} {hi[2]}")

    def flush(self) -> None:
        for cmd in self._to_commands(self._buffer):
            self.command(cmd)
        self._buffer.clear()

    def close(self) -> None:
        self.flush()
        self._conn.disconnect()

    @staticmethod
    def _to_commands(buffer: dict[Vec3, Block]) -> list[str]:
        """Coalesce X-axis runs of the same block into /fill commands."""
        commands: list[str] = []
        remaining = dict(buffer)
        for (x, y, z), block in sorted(
            buffer.items(), key=lambda item: (item[0][1], item[0][2], item[0][0])
        ):
            if (x, y, z) not in remaining:
                continue
            end = x
            while remaining.get((end + 1, y, z)) == block and (end + 1 - x + 1) < FILL_LIMIT:
                end += 1
            for cx in range(x, end + 1):
                remaining.pop((cx, y, z), None)
            if end == x:
                commands.append(f"setblock {x} {y} {z} {block}")
            else:
                commands.append(f"fill {x} {y} {z} {end} {y} {z} {block}")
        return commands
