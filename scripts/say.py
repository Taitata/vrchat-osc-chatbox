
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from osc_chatbox.app import main

if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    if not msg:
        print("Usage: python scripts/say.py \"Your message here\"")
        sys.exit(1)
    main(["--say", msg])
