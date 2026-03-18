"""Module entrypoint for `python -m multiarch_publish`."""

from ._action import main

if __name__ == "__main__":
    raise SystemExit(main())
