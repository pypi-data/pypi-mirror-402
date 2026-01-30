from __future__ import annotations

import sys



def main() -> None:
    from wbal.cli import main as wbal_main

    raise SystemExit(wbal_main(["poll", *sys.argv[1:]]))


if __name__ == "__main__":
    main()
