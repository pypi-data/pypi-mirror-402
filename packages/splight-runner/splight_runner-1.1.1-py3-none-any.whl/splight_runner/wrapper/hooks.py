import atexit

from splight_runner.api.logging_interceptor import interceptor


def flush_logs() -> None:
    """Flushes the log records."""
    interceptor.flush()
    interceptor.stop()


def finish_execution() -> None:
    """Register functions to be executed the process finishes."""

    # Flush logs buffer
    atexit.register(flush_logs)
