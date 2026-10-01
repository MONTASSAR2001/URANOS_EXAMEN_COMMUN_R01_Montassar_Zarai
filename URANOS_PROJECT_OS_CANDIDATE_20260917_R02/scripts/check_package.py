"""Verify built wheel resources against exact source; compilation is not enough."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def inspect_wheel(app_root, wheel):
    app_root, wheel = Path(app_root), Path(wheel)
    package = app_root / "uranos_project_os"
    required = sorted(path for path in package.rglob("*") if path.is_file()
                      and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"})
    if not required:
        raise ValueError("No application package sources found")
    missing, mismatched = [], []
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        for path in required:
            name = path.relative_to(app_root).as_posix()
            if name not in names:
                missing.append(name)
            elif archive.read(name) != path.read_bytes():
                mismatched.append(name)
    return {"wheel": wheel.name, "source_files": len(required), "missing": missing,
            "mismatched": mismatched, "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "pass": not missing and not mismatched}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, default=Path(__file__).resolve().parents[1] / "apps/uranos_project_os")
    parser.add_argument("--wheel", type=Path)
    args = parser.parse_args()
    wheels = [args.wheel] if args.wheel else list((args.app_root / "dist").glob("*.whl"))
    if len(wheels) != 1:
        parser.error("Build exactly one wheel or select an explicit --wheel")
    result = inspect_wheel(args.app_root, wheels[0])
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
