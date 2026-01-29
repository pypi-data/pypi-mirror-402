"""Command-line interface for freezeburn."""

import argparse
import sys
from pathlib import Path

from freezeburn import __version__
from freezeburn.core import generate_requirements, write_requirements


def main() -> int:
    """Main entry point for freezeburn."""
    parser = argparse.ArgumentParser(
        prog="freezeburn",
        description="Freeze what you actually use.",
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Project directory to scan (default: .)",
    )
    parser.add_argument(
        "-o", "--output", default="requirements.txt",
        help="Output file (default: requirements.txt)",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress warnings",
    )
    parser.add_argument(
        "--exclude-submodules", action="store_true",
        help="Skip scanning git submodules",
    )
    parser.add_argument(
        "--include-orphans", action="store_true",
        help="Include orphan packages (installed but not in dependency tree)",
    )
    parser.add_argument(
        "-v", "--version", action="version",
        version=f"freezeburn {__version__}",
    )

    args = parser.parse_args()
    project_path = Path(args.path).resolve()

    if not project_path.is_dir():
        print(f"Error: Not a directory: {project_path}", file=sys.stderr)
        return 1

    print(f"Scanning: {project_path}")
    lines, warnings, orphans = generate_requirements(
        project_path,
        warn_missing=not args.quiet,
        exclude_submodules=args.exclude_submodules,
        include_orphans=args.include_orphans,
    )

    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    if not args.quiet and orphans:
        for name, version in sorted(orphans.items()):
            print(
                f"Orphan: '{name}=={version}' (installed but not in dependency tree)",
                file=sys.stderr,
            )

    write_requirements(lines, Path(args.output))
    print(f"Found {len(lines)} package(s) -> {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
