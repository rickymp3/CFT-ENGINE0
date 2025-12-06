"""Pytest configuration to ensure engine module can be imported."""
import sys
from pathlib import Path

# Add parent directory to Python path so 'engine' module can be imported
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
