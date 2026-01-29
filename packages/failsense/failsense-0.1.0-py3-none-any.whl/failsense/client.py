"""
FailSense SDK Client

Handles error tracking, monitoring, and AI tracer check-ins.
"""

import time
import requests
import threading
import sys
import traceback
from datetime import datetime, timezone


class Client:
    """
    FailSense SDK client for error tracking and monitoring.
    
    Args:
        dsn: API endpoint URL (e.g., https://api.failsense.com)
        api_key: Your FailSense API key from Settings page
    
    Example:
        >>> from failsense import Client
        >>> fs = Client(dsn="https://api.failsense.com", api_key="fs_live_...")
        >>> fs.capture_exception()
    """
    
    def __init__(self, dsn: str, api_key: str = None):
        self.dsn = dsn.rstrip('/')
        self.api_key = api_key
        self._queue = []
        self._breadcrumbs = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def set_api_key(self, api_key: str):
        """Update the API key."""
        self.api_key = api_key

    def add_breadcrumb(self, category: str, message: str, level: str = "info", data: dict = None):
        """
        Add a breadcrumb to track user actions.
        
        Args:
            category: Breadcrumb category (e.g., "navigation", "http")
            message: Descriptive message
            level: Severity level (info, warning, error)
            data: Additional context data
        """
        crumb = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "message": message,
            "level": level,
            "data": data or {}
        }
        with self._lock:
            self._breadcrumbs.append(crumb)
            if len(self._breadcrumbs) > 50:
                self._breadcrumbs.pop(0)

    def capture_exception(self, exc_info=None, context=None, breadcrumbs=None):
        """
        Capture and send an exception to FailSense.
        
        Args:
            exc_info: Exception info tuple (type, value, traceback). If None, uses sys.exc_info()
            context: Additional context dictionary
            breadcrumbs: List of breadcrumbs to attach
        """
        if not exc_info:
            exc_info = sys.exc_info()
        
        exc_type, exc_value, exc_traceback = exc_info
        
        if exc_value is None:
            return

        tb_strings = traceback.format_exception(exc_type, exc_value, exc_traceback)
        stacktrace_str = "".join(tb_strings)
        
        error_type = exc_type.__name__ if exc_type else "UnknownError"
        message = str(exc_value)

        final_breadcrumbs = (self._breadcrumbs.copy()) + (breadcrumbs or [])

        payload = {
            "error_type": error_type,
            "message": message,
            "stacktrace": stacktrace_str,
            "context": context or {},
            "breadcrumbs": self._process_breadcrumbs(final_breadcrumbs),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._enqueue(payload)

    def check_in_monitor(self, monitor_id: int, status: str, metadata: dict = None):
        """
        Send a monitor check-in heartbeat.
        
        Args:
            monitor_id: Monitor ID from FailSense dashboard
            status: "ok" or "error"
            metadata: Additional metadata
        """
        payload = {
            "status": status,
            "metadata": metadata or {}
        }
        threading.Thread(target=self._send_heartbeat, args=(monitor_id, payload), daemon=True).start()

    def monitor(self, llm_client, tracer_id: int):
        """
        Wrap an LLM client to automatically track API calls.
        
        Args:
            llm_client: LLM client instance (e.g., OpenAI())
            tracer_id: AI Tracer ID from FailSense dashboard
        
        Returns:
            Wrapped client that sends check-ins automatically
        
        Example:
            >>> from openai import OpenAI
            >>> raw_client = OpenAI(api_key="sk-...")
            >>> client = fs.monitor(raw_client, tracer_id=1)
            >>> response = client.chat.completions.create(...)
        """
        from .llm import LLMMonitor
        return LLMMonitor(llm_client, self, tracer_id)

    def checkin_ai_tracer(self, tracer_id: int, checkin_data: dict):
        """Send a check-in to an AI Tracer."""
        threading.Thread(
            target=self._send_ai_tracer_checkin, 
            args=(tracer_id, checkin_data),
            daemon=True
        ).start()

    def close(self):
        """Gracefully shutdown the SDK and flush pending events."""
        self._stop_event.set()
        self._worker_thread.join(timeout=2)

    def _process_breadcrumbs(self, breadcrumbs):
        if not breadcrumbs:
            return []
        processed = []
        for crumb in breadcrumbs:
            c = crumb.copy()
            if not c.get('timestamp'):
                c['timestamp'] = datetime.now(timezone.utc).isoformat()
            processed.append(c)
        return processed

    def _enqueue(self, payload):
        with self._lock:
            if len(self._queue) < 100:
                self._queue.append(payload)

    def _worker(self):
        while not self._stop_event.is_set():
            payloads_to_send = []
            with self._lock:
                if self._queue:
                    payloads_to_send = self._queue[:10]
                    self._queue = self._queue[10:]
            
            if payloads_to_send:
                for p in payloads_to_send:
                    self._send(p)
            else:
                time.sleep(0.5)

    def _send(self, payload):
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            url = f"{self.dsn}/api/v1/events"
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception:
            pass

    def _send_heartbeat(self, monitor_id, payload):
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            url = f"{self.dsn}/api/v1/monitors/{monitor_id}/checkin"
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception:
            pass

    def _send_ai_tracer_checkin(self, tracer_id, payload):
        try:
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            url = f"{self.dsn}/api/v1/traces/{tracer_id}/checkin"
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception:
            pass


class MonitorContext:
    """Context manager for monitor check-ins."""
    
    def __init__(self, client: Client, monitor_id: int):
        self.client = client
        self.monitor_id = monitor_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = "error" if exc_type else "ok"
        metadata = {}
        if exc_type:
            tb_strings = traceback.format_exception(exc_type, exc_val, exc_tb)
            stacktrace_str = "".join(tb_strings)
            
            with self.client._lock:
                breadcrumbs = self.client._breadcrumbs.copy()
            
            metadata = {
                "error_type": exc_type.__name__,
                "error_message": str(exc_val),
                "stacktrace": stacktrace_str,
                "breadcrumbs": breadcrumbs
            }
        self.client.check_in_monitor(self.monitor_id, status, metadata)
