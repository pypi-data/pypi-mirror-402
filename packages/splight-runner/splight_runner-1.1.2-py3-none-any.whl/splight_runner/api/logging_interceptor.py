import traceback
from logging import LogRecord

from splight_runner.api.settings import settings
from splight_runner.log_streamer.log_streamer import ComponentLogsStreamer
from splight_runner.logging import log


class ApplicationLogInterceptor:
    """Class responsible for intercept logs records from the logging module
    and append them into a queue for further processing. In particular for
    sending the logs events to Splight GRPC API.
    """

    def __init__(
        self,
        host: str,
        access_id: str,
        secret_key: str,
        process_id: str,
        sender_type: str,
        api_version: str,
    ):
        self._streamer = ComponentLogsStreamer(
            host=host,
            access_id=access_id,
            secret_key=secret_key,
            api_version=api_version,
            process_id=process_id,
        )
        self._sender_type = sender_type
        self._streamer.start()

    def save_record(self, record: LogRecord) -> None:
        """Saves the logging record to be sent.

        Parameters
        ----------
        record: LogRecord
            The log record.
        """
        exc_info = None
        try:
            message = str(record.msg) % record.args
        except Exception as exc:
            log(exc)
            message = str(record.msg)

        if record.exc_info:
            exc_info = "".join(
                traceback.format_exception(*record.exc_info)
            ).replace('"', "'")
            message = str(record.msg)
        else:
            exc_info = ""

        # tags attribute is not default in logger
        tags = None
        if hasattr(record, "tags"):
            tags = getattr(record, "tags")
        event = {
            "sender_type": self._sender_type,
            "name": record.name,
            "message": message,
            "loglevel": record.levelname,
            "filename": record.filename,
            "traceback": exc_info,
            "tags": tags,
        }
        self._streamer.insert_message(event)

    def flush(self) -> None:
        """Flushes the log records."""
        self._streamer.flush()

    def stop(self) -> None:
        """Stops the thread."""
        self._streamer.stop()


interceptor = ApplicationLogInterceptor(
    host=settings.splight_platform_api_host,
    access_id=settings.access_id,
    secret_key=settings.secret_key,
    process_id=settings.process_id,
    sender_type=settings.process_type,
    api_version=settings.api_version,
)
