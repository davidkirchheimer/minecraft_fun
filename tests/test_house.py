import pytest

from minecraft_fun.generators import house


def test_house_has_floor_walls_and_a_door():
    s = house(width=7, depth=7, height=4)
    assert s.get((3, 0, 3)).id == "minecraft:oak_planks"  # floor
    assert s.get((0, 2, 3)).id == "minecraft:oak_planks"  # wall
    assert s.get((3, 1, 0)).id == "minecraft:oak_door"
    assert s.get((3, 2, 0)).states["half"] == "upper"


def test_house_interior_is_hollow():
    s = house(width=9, depth=9, height=5)
    for y in range(1, 5):
        assert s.get((4, y, 4)) is None or s.get((4, y, 4)).id == "minecraft:air"


def test_house_corners_are_logs():
    s = house()
    assert s.get((0, 1, 0)).id == "minecraft:oak_log"


def test_roof_overhangs_the_walls():
    s = house(width=7, depth=7, height=4)
    assert s.bounds.lo[0] == -1
    assert s.bounds.lo[2] == -1
    assert s.bounds.hi[1] > 4


@pytest.mark.parametrize("kwargs", [{"width": 3}, {"depth": 4}, {"height": 2}])
def test_house_rejects_degenerate_sizes(kwargs):
    with pytest.raises(ValueError):
        house(**kwargs)
