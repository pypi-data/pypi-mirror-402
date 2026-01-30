import sys


def log(message: str) -> None:
    """Prints a message to the standard output.

    Parameters
    ----------
    message: str
        The message to be printed.
    """
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()
