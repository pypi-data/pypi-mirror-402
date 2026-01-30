import threading
import queue
import time
import requests
import random
from typing import Optional
from .schemas import RunPayload
from .logger import logger

class BackgroundTransport:
    def __init__(self, api_key: Optional[str], api_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        # Critical Fix 1: Limit queue size to prevent memory leaks
        self._queue: queue.Queue[RunPayload] = queue.Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def send(self, payload: RunPayload):
        try:
            # Critical Fix 1b: Drop events if queue full (fail open)
            self._queue.put_nowait(payload)
        except queue.Full:
            logger.warning("Transport queue full. Dropping event to prevent memory leak.")

    def close(self):
        self._stop_event.set()
        self._thread.join(timeout=2.0)

    def _worker(self):
        while not self._stop_event.is_set():
            try:
                payload = self._queue.get(timeout=1.0)
                self._post_payload_with_retry(payload)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in transport worker: {e}", exc_info=True)

    def _post_payload_with_retry(self, payload: RunPayload, max_retries=3):
        url = f"{self.api_url}/ingest/trajectory" 
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key or "" 
        }
        
        # Pydantic dump
        try:
            data = payload.model_dump(mode='json')
        except Exception as e:
            logger.error(f"Failed to serialize payload: {e}")
            return

        # Critical Fix 2: Retry with exponential backoff
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, json=data, headers=headers, timeout=5)
                if resp.status_code < 400:
                    return # Success
                
                # Server error, strictly retry 5xx, fail on 4xx
                if 400 <= resp.status_code < 500:
                    logger.error(f"API Error {resp.status_code}: {resp.text}")
                    return # Do not retry 4xx errors
                    
                logger.warning(f"Transport retry {attempt+1}/{max_retries} due to {resp.status_code}")
                
            except requests.RequestException as e:
                logger.warning(f"Transport retry {attempt+1}/{max_retries} due to network error: {e}")
            
            # Backoff: 1s, 2s, 4s... with jitter
            sleep_time = (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(sleep_time)
            
        logger.error("Failed to send trace after max retries. Event dropped.")
