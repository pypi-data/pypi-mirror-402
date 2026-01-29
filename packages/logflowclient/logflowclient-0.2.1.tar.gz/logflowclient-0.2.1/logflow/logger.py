"""
LogFlow Logger - Main SDK class
"""

import json
import time
import threading
import queue
import atexit
from typing import Dict, Any, Optional, List, Literal
from urllib.parse import urljoin
import requests

# Valid log types matching the database enum
LogType = Literal['info', 'error', 'warning', 'test']


class Logger:
    """
    LogFlow Logger - Send logs to LogFlow platform
    
    Features:
    - Non-blocking log sending
    - Automatic batching
    - Fail-safe (won't crash your app)
    - Retry logic with exponential backoff
    - Automatic cleanup (no need to call close())
    
    Example:
        logger = Logger(api_key="lf_your_api_key")
        logger.log(bucket="events", data={"user": "123"}, log_type="info")
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://logflow-backend-322267617190.us-central1.run.app",
        batch_size: int = 10,
        flush_interval: float = 5.0,
        max_retries: int = 3,
        debug: bool = False
    ):
        """
        Initialize LogFlow Logger
        
        Args:
            api_key: Your LogFlow API key (automatically determines project)
            api_url: LogFlow API URL (default: production URL)
            batch_size: Number of logs to batch before sending (default: 10)
            flush_interval: Seconds to wait before flushing batch (default: 5.0)
            max_retries: Maximum number of retry attempts (default: 3)
            debug: Enable debug logging (default: False)
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.debug = debug
        
        # Internal state
        self._queue: queue.Queue = queue.Queue()
        self._batch: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._last_flush = time.time()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Register automatic cleanup
        atexit.register(self._cleanup)
        
        # Start background worker
        self._start_worker()
    
    def log(
        self, 
        bucket: str, 
        data: Dict[str, Any], 
        log_type: Optional[LogType] = None
    ) -> None:
        """
        Send a log entry
        
        Args:
            bucket: Log bucket name (e.g., "errors", "user_activity")
            data: JSON-serializable dictionary with log data
            log_type: Type of log - one of: 'info', 'error', 'warning', 'test' (default: 'info')
                      If not provided or invalid, defaults to 'info'
        
        Example:
            logger.log(
                bucket="user_activity",
                data={
                    "event": "button_click",
                    "button_id": "submit",
                    "user_id": "123"
                }
            )
            # Or with explicit type:
            logger.log(bucket="errors", data={"error": "..."}, log_type="error")
        """
        try:
            # Validate and default log_type to 'info' if not provided or invalid
            valid_types = ('info', 'error', 'warning', 'test')
            original_log_type = log_type
            if log_type is None or log_type not in valid_types:
                if self.debug and original_log_type is not None:
                    print(f"[LogFlow] Invalid log_type '{original_log_type}', defaulting to 'info'")
                log_type = "info"
            
            log_entry = {
                "bucket": bucket,
                "log_type": log_type,
                "data": data
            }
            self._queue.put(log_entry)
            
            if self.debug:
                print(f"[LogFlow] Queued log: {bucket} (type: {log_type})")
        
        except Exception as e:
            # Fail-safe: Don't crash the application
            if self.debug:
                print(f"[LogFlow] Error queuing log: {e}")
    
    def flush(self) -> None:
        """
        Force flush all pending logs
        Useful before application shutdown
        """
        if self.debug:
            print("[LogFlow] Flushing logs...")
        
        # Process remaining items in queue
        while not self._queue.empty():
            try:
                log_entry = self._queue.get_nowait()
                with self._lock:
                    self._batch.append(log_entry)
            except queue.Empty:
                break
        
        # Send batch
        self._send_batch()
    
    def _cleanup(self) -> None:
        """Internal cleanup method called automatically on exit"""
        if self.debug:
            print("[LogFlow] Cleaning up...")
        
        # Flush pending logs
        self.flush()
        
        # Stop worker thread
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=10)
    
    def close(self) -> None:
        """
        Manually close the logger and cleanup resources
        Note: This is optional - cleanup happens automatically on exit
        """
        self._cleanup()
    
    def _start_worker(self) -> None:
        """Start background worker thread"""
        self._worker_thread = threading.Thread(
            target=self._worker,
            daemon=True
        )
        self._worker_thread.start()
        
        if self.debug:
            print("[LogFlow] Background worker started")
    
    def _worker(self) -> None:
        """Background worker that processes queue and sends batches"""
        while not self._stop_event.is_set():
            try:
                # Get item from queue (with timeout)
                try:
                    log_entry = self._queue.get(timeout=1.0)
                    
                    with self._lock:
                        self._batch.append(log_entry)
                    
                    # Send batch if size reached
                    if len(self._batch) >= self.batch_size:
                        self._send_batch()
                
                except queue.Empty:
                    pass
                
                # Send batch if interval exceeded
                if time.time() - self._last_flush >= self.flush_interval:
                    if len(self._batch) > 0:
                        self._send_batch()
            
            except Exception as e:
                if self.debug:
                    print(f"[LogFlow] Worker error: {e}")
    
    def _send_batch(self) -> None:
        """Send batch of logs to LogFlow API"""
        with self._lock:
            if not self._batch:
                return
            
            batch = self._batch.copy()
            self._batch.clear()
            self._last_flush = time.time()
        
        if self.debug:
            print(f"[LogFlow] Sending batch of {len(batch)} logs")
        
        # Send with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    urljoin(self.api_url, "/api/v1/ingest/batch"),
                    json=batch,  # Send list directly
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                if response.status_code in (200, 202):  # Accept both 200 and 202
                    if self.debug:
                        print(f"[LogFlow] Batch sent successfully")
                    return
                else:
                    if self.debug:
                        print(f"[LogFlow] API error: {response.status_code} - {response.text}")
            
            except Exception as e:
                if self.debug:
                    print(f"[LogFlow] Send error (attempt {attempt + 1}): {e}")
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        # Failed after all retries
        if self.debug:
            print(f"[LogFlow] Failed to send batch after {self.max_retries} attempts")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.close()
        return False
