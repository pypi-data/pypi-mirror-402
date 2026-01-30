import threading
import queue
import time
import requests # using sync requests in thread
from typing import List, Optional
from lightcurve.schemas import CognitionEvent
from .logger import logger

class EventBuffer:
    def __init__(self, api_url: str, api_key: Optional[str] = None, batch_size: int = 10, flush_interval: float = 2.0):
        self.api_url = api_url
        self.api_key = api_key
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Hardening: Limit queue size
        self._queue: queue.Queue[CognitionEvent] = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def add_event(self, event: CognitionEvent):
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.warning("Event buffer full. Dropping event.")

    def flush(self):
        """Force flush all events in queue."""
        self._queue.join()

    def close(self):
        self._stop_event.set()
        self._worker_thread.join(timeout=5.0)

    def _worker_loop(self):
        batch = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # Wait for items nicely
                try:
                    event = self._queue.get(timeout=0.5)
                    batch.append(event)
                except queue.Empty:
                    pass

                current_time = time.time()
                is_batch_full = len(batch) >= self.batch_size
                is_time_to_flush = (current_time - last_flush) >= self.flush_interval and len(batch) > 0

                if is_batch_full or is_time_to_flush:
                    self._send_batch(batch)
                    # Mark tasks as done in queue
                    for _ in range(len(batch)):
                        self._queue.task_done()
                    batch = []
                    last_flush = current_time

            except Exception as e:
                logger.error(f"Error in buffer worker: {e}", exc_info=True)

        # Final flush on exit
        if batch:
            self._send_batch(batch)

    def _send_batch(self, batch: List[CognitionEvent]):
        try:
            payload = {
                "events": [event.model_dump(mode='json') for event in batch]
            }
            # Hardening: Using /v1/ingest as per existing
            endpoint = f"{self.api_url}/v1/ingest"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code >= 400:
                logger.error(f"Failed to send batch: {response.status_code} {response.text}")
                return
                
        except Exception as e:
            logger.error(f"Failed to send batch: {e}")
