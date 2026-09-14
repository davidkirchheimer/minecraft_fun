from minecraft_fun import Block, Structure
from minecraft_fun.backends.dryrun import DryRunBackend


def test_block_namespaces_and_state_string():
    block = Block("oak_stairs", {"facing": "east", "half": "bottom"})
    assert block.id == "minecraft:oak_stairs"
    assert str(block) == "minecraft:oak_stairs[facing=east,half=bottom]"


def test_fill_hollow_leaves_interior_empty():
    s = Structure().fill((0, 0, 0), (2, 2, 2), Block("stone"), hollow=True)
    assert len(s) == 27 - 1
    assert s.get((1, 1, 1)) is None


def test_rotation_moves_blocks_and_rotates_facing():
    s = Structure().set((1, 0, 0), Block("oak_stairs", {"facing": "north"}))
    rotated = s.rotated_y(1)
    assert rotated.get((0, 0, 1)).states["facing"] == "east"


def test_four_rotations_are_identity():
    s = Structure().fill((0, 0, 0), (3, 1, 2), Block("stone"))
    assert s.rotated_y(4).blocks == s.blocks


def test_mirror_flips_x_and_facing():
    s = Structure().set((2, 0, 0), Block("furnace", {"facing": "east"}))
    mirrored = s.mirrored("x")
    assert mirrored.get((-2, 0, 0)).states["facing"] == "west"


def test_dryrun_backend_records_translated_placements():
    s = Structure().set((0, 0, 0), Block("stone"))
    backend = DryRunBackend()
    assert backend.place_structure(s, (10, 64, -5)) == 1
    assert backend.get_block((10, 64, -5)) == Block("stone")
