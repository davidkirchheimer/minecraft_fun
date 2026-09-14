"""Command line entry point: ``mcfun``."""

from __future__ import annotations

import argparse
import sys

from .backends.dryrun import DryRunBackend
from .generators import GENERATORS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcfun", description="Build structures in Minecraft")
    sub = parser.add_subparsers(dest="command", required=True)

    place = sub.add_parser("place", help="generate a structure and place it")
    place.add_argument("generator", choices=sorted(GENERATORS))
    place.add_argument("--at", nargs=3, type=int, default=[0, 64, 0], metavar=("X", "Y", "Z"))
    place.add_argument("--backend", choices=["dryrun", "rcon"], default="dryrun")
    place.add_argument("--rotate", type=int, default=0, help="quarter turns clockwise")
    place.add_argument("--size", nargs=3, type=int, metavar=("W", "D", "H"))
    place.add_argument("--host", default="127.0.0.1")
    place.add_argument("--port", type=int, default=25575)
    place.add_argument("--password", default=None, help="defaults to $RCON_PASSWORD")
    place.add_argument(
        "--slice", type=int, default=None, help="dryrun: render the XZ plane at this Y"
    )
    return parser


def _open_backend(args: argparse.Namespace):
    if args.backend == "rcon":
        from .backends.rcon import RconBackend

        return RconBackend(host=args.host, password=args.password, port=args.port)
    return DryRunBackend()


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    kwargs = {}
    if args.size:
        kwargs = dict(zip(("width", "depth", "height"), args.size, strict=True))
    structure = GENERATORS[args.generator](**kwargs)
    if args.rotate:
        structure = structure.rotated_y(args.rotate)

    origin = tuple(args.at)
    with _open_backend(args) as backend:
        count = backend.place_structure(structure, origin)
        if isinstance(backend, DryRunBackend):
            y = args.slice if args.slice is not None else origin[1] + 1
            print(backend.render_slice(y))
    print(f"placed {count} blocks at {origin} via {args.backend}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
