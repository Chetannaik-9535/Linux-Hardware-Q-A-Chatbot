"""Root entrypoint for 1-click Streamlit Community Cloud deployment."""

import runpy
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

target = repo_root / "hw_assistant" / "ui" / "streamlit_app.py"
runpy.run_path(str(target), run_name="__main__")
