"""
Launcher script: patches PyTorch BEFORE Streamlit starts to avoid crash.
Usage: python group/run_app.py
"""
import sys
import os

# Step 1: Patch torch._classes BEFORE streamlit imports anything
try:
    import torch
    _orig = torch._classes._ClassesParent.__getattr__
    def _safe(self, attr):
        try:
            return _orig(self, attr)
        except RuntimeError as e:
            raise AttributeError(str(e)) from e
    torch._classes._ClassesParent.__getattr__ = _safe
    print("[Launcher] PyTorch hotpatched successfully.")
except Exception:
    pass

# Step 2: Launch Streamlit programmatically
from streamlit.web import cli as stcli

sys.argv = [
    "streamlit", "run",
    os.path.join(os.path.dirname(__file__), "app.py"),
    "--server.headless", "true",
    "--server.fileWatcherType", "none",
]
stcli.main()
