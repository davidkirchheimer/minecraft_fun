from minecraft_fun import Block, Structure
from minecraft_fun.backends.rcon import RconBackend


def test_runs_of_identical_blocks_become_fill_commands():
    s = Structure().fill((0, 64, 0), (4, 64, 0), Block("stone"))
    commands = RconBackend._to_commands(s.blocks)
    assert commands == ["fill 0 64 0 4 64 0 minecraft:stone"]


def test_differing_blocks_stay_setblock():
    blocks = {(0, 64, 0): Block("stone"), (1, 64, 0): Block("dirt")}
    commands = RconBackend._to_commands(blocks)
    assert sorted(commands) == [
        "setblock 0 64 0 minecraft:stone",
        "setblock 1 64 0 minecraft:dirt",
    ]


def test_blockstates_are_part_of_the_command():
    blocks = {(0, 64, 0): Block("oak_stairs", {"facing": "east"})}
    assert RconBackend._to_commands(blocks) == ["setblock 0 64 0 minecraft:oak_stairs[facing=east]"]
