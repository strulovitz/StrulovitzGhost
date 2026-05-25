"""ITG Logger — structured logging for the Image To Ghost pipeline.

Every ITG operation logs: timestamp, node_id, task_id, event, details.
Writes to: src/logs/itg_YYYYMMDD_HHMMSS.log (new file per session).
Also prints to stderr for real-time terminal visibility.
"""

import os
import sys
import time
import threading
from datetime import datetime

_log_file = None
_log_lock = threading.Lock()

ITG_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(ITG_LOG_DIR, exist_ok=True)

def _init_log():
    global _log_file
    if _log_file is not None:
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file = open(os.path.join(ITG_LOG_DIR, f"itg_{ts}.log"), "a", encoding="utf-8", buffering=1)
    _log_file.write(f"=== ITG Pipeline Log Started: {datetime.now().isoformat()} ===\n")
    _log_file.write(f"    PID: {os.getpid()}\n\n")


def itg_log(node_id, event, task_id=None, detail=""):
    """Log an ITG event with structured fields.
    
    Args:
        node_id: Which node (boss-laptop, worker-desktop, etc.)
        event: What happened (SPLIT_START, SPLIT_DONE, JUDGE, CLAIM, UPLOAD, CHILDREN_CREATED, etc.)
        task_id: The task ID if applicable
        detail: Additional info (timing, filenames, errors)
    """
    _init_log()
    ts = time.strftime("%H:%M:%S")
    tid = f"task={task_id}" if task_id else "task=?"
    line = f"[{ts}] {node_id} | {event:20s} | {tid:12s} | {detail}\n"
    with _log_lock:
        _log_file.write(line)
        _log_file.flush()
        try:
            sys.stderr.write(line)
        except Exception:
            pass


def itg_error(node_id, event, task_id=None, error=""):
    """Log an ITG error with ERROR: prefix for easy search."""
    itg_log(node_id, f"ERROR:{event}", task_id, str(error)[:200])


def itg_close():
    global _log_file
    if _log_file:
        with _log_lock:
            _log_file.write(f"\n=== ITG Pipeline Log Ended: {datetime.now().isoformat()} ===\n")
            _log_file.close()
            _log_file = None
