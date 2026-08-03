import sys
from pathlib import Path

# Ensure "src" is on sys.path so "import blindspot" works
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from blindspot.__main__ import main  # absolute import into package

if __name__ == "__main__":
    main()