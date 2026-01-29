import os
import sys
import time
import socket
import hashlib
import threading
import logging
import json

logger = logging.getLogger("CactusCat.Guard")

class ProcessGuard:
    """
    Stabilization utilities: Single Instance enforcement and Dead Man's Switch.
    """
    def __init__(self, app):
        self.app = app
        self._instance_socket = None
        self._running = False

    def enforce_single_instance(self, app_id: str):
        """
        Ensures only one instance of the app runs. 
        If a second launches, it notifies the first and exits.
        """
        # Generate a stable port between 10000-60000 based on app_id
        port = 10000 + (int(hashlib.md5(app_id.encode()).hexdigest(), 16) % 50000)
        
        try:
            # Try to bind to the port
            self._instance_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._instance_socket.bind(("127.0.0.1", port))
            self._instance_socket.listen(1)
            
            # Start background listener
            thread = threading.Thread(target=self._listen_loop, daemon=True)
            thread.start()
            logger.debug(f"Single instance lock acquired on port {port}")
            return True
        except socket.error:
            # Instance already exists!
            logger.info("Another instance is already running. Notifying and exiting...")
            self._notify_primary_instance(port)
            sys.exit(0)

    def _listen_loop(self):
        while True:
            try:
                conn, _ = self._instance_socket.accept()
                with conn:
                    data = conn.recv(1024).decode('utf-8')
                    if data:
                        try:
                            payload = json.loads(data)
                            # Tell the app to focus and handle arguments
                            self.app.bus.emit("second_instance", payload.get("args", []))
                            if self.app.handle:
                                self.app.handle.restore()
                                self.app.handle.set_focus()
                        except: pass
            except: break

    def _notify_primary_instance(self, port):
        """Sends current CLI args to the primary instance."""
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1) as s:
                s.sendall(json.dumps({
                    "args": sys.argv[1:],
                    "pid": os.getpid()
                }).encode('utf-8'))
        except: pass

    def start_dead_mans_switch(self, interval=2.0):
        """
        Monitors the parent/engine process. If the engine dies,
        this python process will exit immediately.
        """
        # In CactusCat, the Rust engine is the parent of the Python process
        # when launched via the bootloader, OR it's a sibling.
        # However, we can monitor the main handle effectively.
        def _monitor():
            while True:
                time.sleep(interval)
                # Check if the native handle is still connected
                if self.app.handle is None and getattr(self.app, '_started', False):
                    # If we started but handle is gone, engine likely closed
                    logger.warning("Native engine handle lost. Triggering Dead Man's Switch.")
                    os._exit(0)
        
        threading.Thread(target=_monitor, daemon=True).start()
