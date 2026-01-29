import os
import sys
import logging
import threading
import time
from collections import deque
from typing import Dict, List, Any, Optional

try:
    import psutil
except ImportError:
    psutil = None

class DequeHandler(logging.Handler):
    """A logging handler that stores logs in a fixed-size queue."""
    def __init__(self, maxlen=500):
        super().__init__()
        self.logs = deque(maxlen=maxlen)

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append({
            "time": time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage()
        })

class Inspector:
    """
    Monitoring and debugging subsystem.
    Tracks IPC calls, logs, and system performance.
    """
    def __init__(self, app_name: str = "CactusCat"):
        self.app_name = app_name
        self.ipc_history = deque(maxlen=200)
        self.log_handler = DequeHandler()
        self.log_handler.setFormatter(logging.Formatter('%(message)s'))
        
        # Attach to root logger to capture everything
        logging.getLogger().addHandler(self.log_handler)
        
        self._stats_thread = None
        self._running = False
        self.current_stats = {}

    def start_telemetry(self, interval=2.0):
        """Starts a background thread to collect CPU and Memory usage."""
        if not psutil:
            logging.warning("psutil not installed. Telemetry disabled.")
            return

        self._running = True
        self._stats_thread = threading.Thread(target=self._stats_loop, args=(interval,), daemon=True)
        self._stats_thread.start()

    def _stats_loop(self, interval):
        process = psutil.Process(os.getpid())
        while self._running:
            try:
                with process.oneshot():
                    cpu = process.cpu_percent()
                    mem = process.memory_info().rss / (1024 * 1024)  # MB
                    threads = process.num_threads()
                
                self.current_stats = {
                    "cpu": cpu,
                    "memory": round(mem, 2),
                    "threads": threads,
                    "uptime": round(time.time() - process.create_time(), 1)
                }
            except Exception as e:
                logging.error(f"Telemetry error: {e}")
            
            time.sleep(interval)

    def record_ipc(self, method: str, args: Any, result: Any, error: Optional[str] = None):
        """Tracks an IPC call between Frontend and Backend."""
        entry = {
            "timestamp": time.time(),
            "method": method,
            "args": args,
            "result": result,
            "error": error
        }
        self.ipc_history.append(entry)

    def get_snapshot(self) -> Dict[str, Any]:
        """Returns a full state snapshot for the DevTools/Inspector UI."""
        return {
            "app_name": self.app_name,
            "stats": self.current_stats,
            "logs": list(self.log_handler.logs),
            "ipc": list(self.ipc_history),
            "python_version": sys.version,
            "platform": sys.platform
        }

    def stop(self):
        self._running = False
