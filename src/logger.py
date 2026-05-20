import sys
import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"strulovitz_{datetime.now().strftime('%Y%m%d')}.log")


class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


def setup_logging():
    log = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
    log.write(f"\n{'='*60}\n")
    log.write(f"Started: {datetime.now().isoformat()}\n")
    log.write(f"{'='*60}\n\n")
    sys.stdout = Tee(sys.stdout, log)
    sys.stderr = Tee(sys.stderr, log)
    return log
