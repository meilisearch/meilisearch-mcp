import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import threading
from queue import Queue
import asyncio


class AsyncLogHandler:
    """Asynchronous log handler with buffering"""

    def __init__(self, max_buffer: int = 1000):
        self.buffer = Queue(maxsize=max_buffer)
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def _worker(self):
        """Background worker to process logs"""
        while self.running:
            try:
                record = self.buffer.get(timeout=1.0)
                self._write_log(record)
            except:
                continue

    def _write_log(self, record: Dict[str, Any]):
        """Write log record to storage"""
        raise NotImplementedError

    def emit(self, record: Dict[str, Any]):
        """Add log record to buffer"""
        try:
            self.buffer.put(record, block=False)
        except:
            pass  # Buffer full, skip log

    def shutdown(self):
        """Shutdown the handler"""
        self.running = False
        self.worker_thread.join()


class FileLogHandler(AsyncLogHandler):
    """File-based log handler"""

    def __init__(self, log_dir: str):
        super().__init__()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_file = None
        self._rotate_file()

    def _rotate_file(self):
        """Rotate log file daily"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.current_file = self.log_dir / f"meilisearch-mcp-{date_str}.log"

    def _write_log(self, record: Dict[str, Any]):
        """Write log record to file"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if not self.current_file or current_date not in self.current_file.name:
            self._rotate_file()

        with open(self.current_file, "a") as f:
            f.write(json.dumps(record) + "\n")


class MCPLogger:
    """Enhanced MCP logger with structured logging"""

    def __init__(self, name: str = "meilisearch-mcp", log_dir: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self._setup_logger(log_dir)

    def _setup_logger(self, log_dir: Optional[str]):
        """Configure logging with multiple handlers"""
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # File handler for structured logging
            if log_dir:
                self.file_handler = FileLogHandler(log_dir)

            self.logger.setLevel(logging.INFO)

    def _log(self, level: str, msg: str, **kwargs):
        """Create structured log entry"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": msg,
            **kwargs,
        }

        # Log to console
        getattr(self.logger, level.lower())(msg)

        # Log structured data to file
        if hasattr(self, "file_handler"):
            self.file_handler.emit(log_entry)

    def debug(self, msg: str, **kwargs):
        self._log("DEBUG", msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log("INFO", msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log("WARNING", msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log("ERROR", msg, **kwargs)

    def shutdown(self):
        """Clean shutdown of logger"""
        if hasattr(self, "file_handler"):
            self.file_handler.shutdown()
