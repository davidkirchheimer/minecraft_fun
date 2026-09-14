# minecraft-fun

Build structures in Minecraft (Java Edition) from Python — either into a live
world or, eventually, straight into a save file.

Structures are described once, independently of how they reach the world, and
written through swappable backends.

## Status

| Backend | Transport | Status |
|---|---|---|
| `dryrun` | in-memory, ASCII preview | working |
| `rcon` | RCON to a vanilla/Paper server | working, write-only |
| `gdmc` | GDMC HTTP Interface mod via `gdpc` | planned |
| `anvil` | direct save-file editing via `amulet-core` | planned |

No Java code is needed for any of these. The GDMC path uses a prebuilt mod jar;
everything else talks to the server or to the save files directly.

## Quick start

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
mcfun place house --at 0 64 0                 # preview, no Minecraft needed
```

```
.#*+=+*#.
.+.....+.
.*.....*.
.+.....+.
.#*+++*#.
#=oak_log  *=glass_pane  +=oak_planks  ==oak_door
```

Against a live server with RCON enabled (`enable-rcon=true`, `rcon.port`,
`rcon.password` in `server.properties`):

```bash
pip install -e ".[rcon]"
export RCON_PASSWORD=...
mcfun place house --at 100 64 -200 --backend rcon --rotate 1
```

## Library use

```python
from minecraft_fun import Block
from minecraft_fun.generators import house
from minecraft_fun.backends.rcon import RconBackend

tower = house(width=9, depth=9, height=6).rotated_y(2)

with RconBackend(host="127.0.0.1") as world:
    world.forceload((100, 64, -200), (110, 80, -190))
    world.place_structure(tower, at=(100, 64, -200))
```

Positions absent from a `Structure` are left untouched when it is placed; place
an explicit `Block("air")` to carve space out.

## Notes on the backends

- **RCON** cannot read the world, so structures can't adapt to terrain there.
  Consecutive identical blocks along X are coalesced into `/fill` commands to
  keep the command count down, and target chunks must be force-loaded.
- **GDMC HTTP** (planned) is the one to use for anything terrain-aware: it reads
  blocks, biomes and heightmaps, batches writes, and works in singleplayer.
- **Anvil** (planned) edits `region/*.mca` offline. The world must not be open
  in Minecraft, or the game will overwrite the edits on its next save.

## Development

```bash
.venv/bin/pytest
.venv/bin/ruff check .
```
