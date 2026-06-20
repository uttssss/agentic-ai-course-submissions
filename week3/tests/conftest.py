"""Make `import copilot...` resolve when running pytest from anywhere."""
import pathlib
import sys

# parents[2]: tests -> copilot -> project root (the dir containing copilot/)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
