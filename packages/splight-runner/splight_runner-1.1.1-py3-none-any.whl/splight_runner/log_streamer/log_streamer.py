import sys
import traceback
from threading import Event, Lock, Thread
from time import sleep
from typing import Optional

from splight_runner.log_streamer.log_buffer import LogsBuffer
from splight_runner.log_streamer.log_client import LogClient


class LogsStreamerError(Exception):
    pass


class ComponentLogsStreamer:
    """Class responsible for sending logs events using GRPC.

    Each log event is inserted into a queue so a separate thread consume
    that queue and send each event to GRPC API.
    """

    _LOG_BUFFER_SIZE = 100
    _LOG_BUFFER_TIMEOUT = 30  # seconds
    _SLEEP_TIME_FOR_RETRY = 1  # seconds

    def __init__(
        self,
        host: str,
        access_id: str,
        secret_key: str,
        api_version: str,
        process_id: Optional[str] = None,
    ):
        self._process_id = process_id

        self._client = LogClient(
            host=host,
            access_id=access_id,
            secret_key=secret_key,
            api_version=api_version,
        )
        self._thread: Thread = Thread(target=self._run, daemon=True)
        self._buffer = LogsBuffer(
            buffer_size=self._LOG_BUFFER_SIZE,
            buffer_timeout=self._LOG_BUFFER_TIMEOUT,
        )
        self._lock = Lock()
        self._running: Event = Event()

    def insert_message(self, message: str) -> None:
        """Insert a log event into the queue.

        Parameters
        ----------
        message: str
            The log message.

        Returns
        -------
        None
        """
        with self._lock:
            message.update({"id": self._process_id})
            self._buffer.add_logs(message)

    def start(self) -> None:
        """Starts the thread for sending logs events"""
        self._running.set()
        self._thread.start()

    def stop(self) -> None:
        """Stops thread."""
        self._running.clear()
        self._thread.join(timeout=10)
        self._buffer.reset()
        self._thread = None

    def flush(self):
        with self._lock:
            self._client.send_logs(self._buffer.data)
            self._buffer.reset()

    def _run(self):
        while self._running.is_set():
            if self._buffer.should_flush():
                try:
                    self._client.send_logs(self._buffer.data)
                except Exception:
                    # If there is any error sending logs, show the error and
                    # wait to retry
                    traceback.print_exc(file=sys.stderr)
                self._buffer.reset()
            sleep(self._SLEEP_TIME_FOR_RETRY)
