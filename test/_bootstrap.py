import sys
from pathlib import Path


def _apply_sys_path() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    for path in (str(root), str(src)):
        if path not in sys.path:
            sys.path.insert(0, path)


_apply_sys_path()
