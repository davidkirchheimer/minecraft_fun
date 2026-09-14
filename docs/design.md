# minecraft-fun — how to connect to Minecraft, and proposed design

## TL;DR

You almost certainly don't need to write any Java. There are three mature paths,
all driven from pure Python:

| Mode | Transport | Python lib | Needs a mod? | Reads blocks? |
|---|---|---|---|---|
| Live, vanilla server | RCON (TCP) | `mcrcon` | no | no (write-only) |
| Live, singleplayer or server | HTTP on localhost:9000 | `gdpc` | yes (prebuilt jar, no coding) | yes |
| Offline save file | direct Anvil/NBT file I/O | `amulet-core` | no | yes |

The only Java artifact involved is a *prebuilt* mod jar you drop into a mods
folder. No JNI, no py4j/jpype bridge, no wrapper to write. Java only comes back
if we later want gameplay hooks (custom blocks, events, commands), which would
mean a small Fabric mod — worth deferring.

---

## Path A — Live edits via RCON (simplest, zero mods)

Minecraft Java dedicated servers speak the Source RCON protocol. In
`server.properties`:

```
enable-rcon=true
rcon.port=25575
rcon.password=<something>
```

Then from Python:

```python
from mcrcon import MCRcon
with MCRcon("127.0.0.1", PASSWORD, port=25575) as mcr:
    mcr.command("setblock 10 64 10 minecraft:stone")
    mcr.command("fill 0 64 0 9 68 9 minecraft:oak_planks hollow")
```

Strengths: nothing to install on the Minecraft side, works over the network,
works against any vanilla/Paper server.

Limits worth knowing up front:
- **Write-only.** You cannot read what's already in the world (no terrain
  sampling, so structures can't adapt to the ground they land on).
- `/fill` is capped at 32768 blocks per command; big builds become thousands of
  round-trips, each one a command-dispatch through the server tick.
- Target chunks must be loaded, or the edit is dropped — use `/forceload` first.
- **Not available in singleplayer.** Singleplayer has commands but no RCON
  listener, and "Open to LAN" doesn't add one.

Useful vanilla commands beyond setblock/fill: `/clone`, `/place structure`
(places a registered structure), `/place template` (places an `.nbt` structure
file from a datapack), `/forceload`, `/summon`, `/data merge block` (for block
entities like chests and signs).

## Path B — Live edits via the GDMC HTTP Interface mod (recommended for real work)

The GDMC (Generative Design in Minecraft) community built exactly this use
case: an external program procedurally generating buildings in a live world.

- Mod: `Niels-NTG/gdmc_http_interface` — a Fabric/Forge mod that opens an HTTP
  server on `localhost:9000` when a world is loaded, with endpoints for
  `GET/PUT /blocks`, biomes, heightmaps, chunks, entities, and running commands.
- Python client: `gdpc` (Generative Design Python Client, v8.1.0, Apr 2025).

```python
from gdpc import Editor, Block, geometry
editor = Editor(buffering=True)          # batches writes, far faster than RCON
ground = editor.getBlock((0, 63, 0))     # you can READ the world
geometry.placeCuboid(editor, (0, 64, 0), (9, 68, 9), Block("oak_planks"))
editor.flushBuffer()
```

Strengths: bidirectional, batched (orders of magnitude faster than one command
per block), gives heightmaps and biomes so structures can be terrain-adaptive,
and it works in **singleplayer** as well as on a server. This is the path I'd
build the interesting features on.

Cost: you install a mod jar (matched to your Minecraft version + Fabric/Forge
loader). No Java code from us.

## Path C — Offline save-file editing

Java Edition worlds are the Anvil format: `region/r.<x>.<z>.mca` files holding
32x32 chunks each, chunks stored as compressed NBT.

- `amulet-core` (v1.9.45) is the library behind the Amulet Map Editor. It
  abstracts over Minecraft versions with a universal block format and
  translation layer, which is the part you really don't want to hand-roll —
  block IDs and chunk NBT layout have changed repeatedly (flattening in 1.13,
  chunk format changes in 1.18 with negative Y, etc.).
  Note: it requires **Python >= 3.11**.
- `nbtlib` / `amulet-nbt` for raw NBT if we need to touch `level.dat` or write
  `.nbt` structure files directly.
- `anvil-parser` exists but is unmaintained since 2021 — I'd avoid it.

Hard rule: **the world must not be open in Minecraft.** The game keeps chunks in
memory and will overwrite your edits on its next save. The tool should refuse to
write if a `session.lock` is held, and should snapshot the region files it is
about to modify.

## Proposed project structure

The key idea: define structures once, independently of how they get into the
world, then have swappable backends.

```
minecraft_fun/
  blocks.py                 # Block: id + blockstate props + optional NBT
  structure.py              # Structure: sparse {(x,y,z): Block}, palette,
                            #   .rotate(), .mirror(), .translate(), .merge()
  generators/               # the fun part: parametric builders
    house.py  tower.py  maze.py  bridge.py
  io/
    nbt_structure.py        # read/write vanilla .nbt structure-block files
    schematic.py            # optional: .schem (WorldEdit/Sponge)
  backends/
    base.py                 # Protocol: get_block, place_block, place_structure,
                            #   flush, bounds
    rcon.py                 # Path A
    gdmc_http.py            # Path B (wraps gdpc)
    anvil.py                # Path C (wraps amulet-core)
    dryrun.py               # in-memory; renders ASCII/PNG slices — lets us
                            #   unit-test every generator with no Minecraft
  cli.py                    # `mcfun place house --at 0 64 0 --backend gdmc`
tests/
```

`dryrun` matters more than it sounds: it means the whole generator layer is
testable in CI without a game running, and you can preview a build before
committing it to your world.

## Suggested build order

1. `Block` / `Structure` core + `dryrun` backend + one generator (a house), with
   tests. No Minecraft needed.
2. `rcon` backend — first real blocks in a live world, minimal setup.
3. `gdmc_http` backend — terrain-aware placement, fast batch writes.
4. `anvil` backend — offline save editing, with locking + backups.
5. Nice-to-haves: import/export `.nbt` structures, a Streamlit or CLI previewer,
   randomized settlement layouts.

## Open questions for you

1. Which Minecraft **Java Edition version** do you play (e.g. 1.21.x)? It
   determines the GDMC mod build and the amulet translation target.
2. Singleplayer, or do you run a **dedicated server**? (Singleplayer rules out
   RCON and pushes us to Path B first.)
3. Fabric or Forge — or no mods installed today?
4. Which do you want working first: **live placement** or **save-file editing**?
5. Repo private or public?
