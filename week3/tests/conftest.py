
import sys
from pathlib import Path

WEEK3_DIR = Path(__file__).resolve().parents[1]

if str(WEEK3_DIR) not in sys.path:
    sys.path.insert(0, str(WEEK3_DIR))
