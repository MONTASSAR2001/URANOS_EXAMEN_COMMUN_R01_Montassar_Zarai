import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
app_path = root / "apps" / "uranos_project_os"
if str(app_path) not in sys.path:
    sys.path.insert(0, str(app_path))
