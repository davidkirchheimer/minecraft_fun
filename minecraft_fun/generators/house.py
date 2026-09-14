"""A parametric small house."""

from __future__ import annotations

from ..blocks import AIR, Block
from ..structure import Structure

DEFAULT_PALETTE = {
    "floor": Block("oak_planks"),
    "wall": Block("oak_planks"),
    "corner": Block("oak_log", {"axis": "y"}),
    "roof": Block("oak_stairs"),
    "ridge": Block("oak_planks"),
    "door": Block("oak_door"),
    "window": Block("glass_pane"),
    "light": Block("lantern", {"hanging": "true"}),
}


def house(
    width: int = 7,
    depth: int = 7,
    height: int = 4,
    palette: dict[str, Block] | None = None,
) -> Structure:
    """A house with its (0, 0, 0) anchor at the front-left floor corner.

    The door faces north (towards -Z). ``height`` is the wall height, excluding
    the gabled roof.
    """
    if width < 5 or depth < 5:
        raise ValueError("house needs width and depth of at least 5")
    if height < 3:
        raise ValueError("house needs a wall height of at least 3")

    p = {**DEFAULT_PALETTE, **(palette or {})}
    s = Structure(name="house")
    x1, z1 = width - 1, depth - 1

    s.fill((0, 0, 0), (x1, 0, z1), p["floor"])
    s.fill((1, 1, 1), (x1 - 1, height - 1, z1 - 1), AIR)  # keep the interior clear
    for y in range(1, height):
        s.fill((0, y, 0), (x1, y, 0), p["wall"])
        s.fill((0, y, z1), (x1, y, z1), p["wall"])
        s.fill((0, y, 0), (0, y, z1), p["wall"])
        s.fill((x1, y, 0), (x1, y, z1), p["wall"])
    s.fill((0, height, 0), (x1, height, z1), p["floor"])  # ceiling

    for cx in (0, x1):
        for cz in (0, z1):
            s.fill((cx, 1, cz), (cx, height - 1, cz), p["corner"])

    door_x = width // 2
    s.set((door_x, 1, 0), p["door"].with_states(half="lower", facing="north"))
    s.set((door_x, 2, 0), p["door"].with_states(half="upper", facing="north"))

    window_y = 2
    for wx in (door_x - 2, door_x + 2):
        s.set((wx, window_y, 0), p["window"])
        s.set((wx, window_y, z1), p["window"])
    for wz in (depth // 2 - 1, depth // 2 + 1):
        s.set((0, window_y, wz), p["window"])
        s.set((x1, window_y, wz), p["window"])

    s.set((1, height - 1, 1), p["light"])
    _gable_roof(s, width, depth, height, p)
    return s


def _gable_roof(s: Structure, width: int, depth: int, height: int, p: dict[str, Block]) -> None:
    """A gabled roof ridged along the Z axis, overhanging one block on every side."""
    half = (width - 1) // 2
    for step in range(half + 1):
        y = height + 1 + step
        left = step - 1
        right = width - step
        for z in range(-1, depth + 1):
            s.set((left, y, z), p["roof"].with_states(facing="east", half="bottom"))
            s.set((right, y, z), p["roof"].with_states(facing="west", half="bottom"))
        # close the triangular gable ends so the attic is not open to the sky
        for gx in range(left + 1, right):
            s.set((gx, y, 0), p["wall"])
            s.set((gx, y, depth - 1), p["wall"])

    ridge_y = height + 1 + half
    for z in range(-1, depth + 1):
        s.set((half, ridge_y, z), p["ridge"])
