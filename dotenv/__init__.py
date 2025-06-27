import os
from pathlib import Path

def load_dotenv(dotenv_path: str = None):
    path = Path(dotenv_path or '.env')
    if not path.is_file():
        return False
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key, value)
    return True
