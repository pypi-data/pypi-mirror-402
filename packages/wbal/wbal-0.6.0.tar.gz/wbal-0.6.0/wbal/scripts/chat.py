from __future__ import annotations

import sys

from wbal.cli import main as wbal_main


def main() -> None:
    raise SystemExit(wbal_main(["chat", *sys.argv[1:]]))


if __name__ == "__main__":
    main()
