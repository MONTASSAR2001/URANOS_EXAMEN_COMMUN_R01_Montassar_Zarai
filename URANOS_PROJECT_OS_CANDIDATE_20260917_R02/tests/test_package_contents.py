"""Small synthetic package checks; actual app wheel is checked after build."""
import importlib.util
from pathlib import Path
from zipfile import ZipFile

import pytest

spec = importlib.util.spec_from_file_location("package_check", Path(__file__).resolve().parents[1] / "scripts/check_package.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize("content,expected", [(b"exact", True), (b"stale", False), (None, False)])
def test_wheel_requires_exact_current_resources(tmp_path, content, expected):
    package = tmp_path / "uranos_project_os"
    package.mkdir()
    (package / "schema.json").write_bytes(b"exact")
    wheel = tmp_path / "demo.whl"
    with ZipFile(wheel, "w") as archive:
        if content is not None:
            archive.writestr("uranos_project_os/schema.json", content)
    result = module.inspect_wheel(tmp_path, wheel)
    assert result["pass"] is expected
    assert result["source_files"] == 1
    assert bool(result["missing"]) is (content is None)
    assert bool(result["mismatched"]) is (content == b"stale")
