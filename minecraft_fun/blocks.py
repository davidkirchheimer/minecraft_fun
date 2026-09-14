"""Version-agnostic block representation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

_ROTATE_Y_90 = {"north": "east", "east": "south", "south": "west", "west": "north"}
_MIRROR_X = {"east": "west", "west": "east"}
_MIRROR_Z = {"north": "south", "south": "north"}


@dataclass(frozen=True)
class Block:
    """A block id, its blockstate properties, and optional block-entity data.

    ``id`` may be given with or without the ``minecraft:`` namespace.
    """

    id: str
    states: Mapping[str, str] = field(default_factory=dict)
    data: str | None = None

    def __post_init__(self) -> None:
        if ":" not in self.id:
            object.__setattr__(self, "id", f"minecraft:{self.id}")
        object.__setattr__(self, "states", dict(self.states))

    @property
    def state_string(self) -> str:
        if not self.states:
            return ""
        inner = ",".join(f"{k}={v}" for k, v in sorted(self.states.items()))
        return f"[{inner}]"

    def with_states(self, **states: str) -> Block:
        return Block(self.id, {**self.states, **states}, self.data)

    def rotated_y(self, quarter_turns: int) -> Block:
        """Return this block with direction-like properties rotated about the Y axis."""
        turns = quarter_turns % 4
        if turns == 0:
            return self
        states = dict(self.states)
        for key in ("facing", "rotation_facing"):
            value = states.get(key)
            if value in _ROTATE_Y_90:
                for _ in range(turns):
                    value = _ROTATE_Y_90[value]
                states[key] = value
        axis = states.get("axis")
        if axis in ("x", "z") and turns % 2 == 1:
            states["axis"] = "z" if axis == "x" else "x"
        return Block(self.id, states, self.data)

    def mirrored(self, axis: str) -> Block:
        table = _MIRROR_X if axis == "x" else _MIRROR_Z
        facing = self.states.get("facing")
        if facing not in table:
            return self
        return self.with_states(facing=table[facing])

    def __str__(self) -> str:
        return f"{self.id}{self.state_string}"


AIR = Block("air")
