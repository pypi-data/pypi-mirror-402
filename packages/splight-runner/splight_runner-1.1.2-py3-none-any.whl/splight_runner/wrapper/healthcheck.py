from typing import Callable, Tuple

from splight_runner.api.component_reporter import reporter


def healthcheck_wrapper(func: Callable) -> Callable:
    """Wrapper for healthcheck method of the Splight Engine

    Parameters
    ----------
    func: Callable
        The original healthcheck method.

    Returns
    -------
    Callable: The wrapped healthcheck method with extra functionality.
    """

    def wrapped(self) -> Tuple[bool, str]:
        is_alive, status = func(self)
        reporter.report_status(status)
        return (is_alive, status)

    return wrapped
