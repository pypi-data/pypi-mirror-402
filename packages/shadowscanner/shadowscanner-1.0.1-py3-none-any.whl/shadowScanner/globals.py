from pathlib import Path

BASE_DIR = Path.home() / ".cache" / "shadowScanner"
BASE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_FILE = BASE_DIR / "cache.json"
TARGETS_FILE = BASE_DIR / "targets.txt"