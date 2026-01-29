import inspect
import sys
from typing import Any, Callable, Dict, List, Optional


class MissingCommandError(Exception):
    """Exception"""

    ...


class MissingArgument(Exception):
    """Exception raises when there is a missing argument for a command"""

    ...


class CommandAdmin:
    """Class respobsible for taking registry of all the commands and callbaks"""

    def __init__(self, name: str, version: str):
        """Constructor

        Parameters
        ----------
        name : str
            Name of the application
        version : str
            The application version
        """
        self._name = name
        self._version = version
        self._commands: Dict[str, Callable] = {}
        self._callback: Dict[str, Callable] = {}

    def command(self, name: Optional[str] = None) -> Callable:
        """Decorator to register a command

        Parameters
        ----------
        name: Optional[str]
            The name for the command

        Returns
        -------
        Callable
            The decorated function
        """

        def decorator(func: Callable) -> Callable:
            func_name = name or func.__name__
            self._commands.update({func_name: func})
            return func

        return decorator

    def callback(self, name: Optional[str] = None) -> Callable:
        """Decorator to register a callback

        Parameters
        ----------
        name: Optional[str]
            The name for the command

        Returns
        -------
        Callable
            The decorated function
        """

        def decorator(func: Callable) -> Callable:
            func_name = name or func.__name__
            self._callback.update({func_name: func})
            return func

        return decorator

    def print_commands(self) -> None:
        """Prints the commands and callbacks"""
        title = f"{self._name} - {self._version}\n"
        sys.stdout.write(title)
        sys.stdout.write("{:=<{}}\n".format("", len(title)))
        sys.stdout.write("Commands:\n")
        for command in self._commands:
            sys.stdout.write(f"{command: >20}\n")
        sys.stdout.write("Callbacks:\n")
        for callback in self._callback:
            name = f"--{callback}"
            sys.stdout.write(f"{name: >20}\n")

    def __call__(self, *args: Any, **kwargs: Any):
        """Dunder method to run a given command."""
        if len(sys.argv) == 1:
            raise MissingCommandError("No command provided")

        command_name = sys.argv[1]
        raw_args = sys.argv[2:]
        if command_name.startswith("--"):
            command = self._retrieve_callback(command_name.lstrip("--"))
        else:
            command = self._retrieve_command(command_name)

        signature = inspect.signature(command)
        command_args = self._parse_arguments(raw_args, signature=signature)
        command(**command_args)

    def _parse_arguments(
        self, raw_args: List, signature: inspect.Signature
    ) -> Dict:
        arguments = {}
        for idx, (name, parameter) in enumerate(signature.parameters.items()):
            try:
                raw_value = raw_args[idx]
            except IndexError as exc:
                raise MissingArgument(f"Missing argument {name}") from exc

            argument = (
                raw_value.split("=")[-1] if "=" in raw_value else raw_value
            )
            arg_value = parameter.annotation(argument)
            arguments.update({name: arg_value})
        return arguments

    def _retrieve_command(self, command_name: str) -> Callable:
        try:
            command = self._commands[command_name]
        except KeyError as exc:
            sys.stderr.write(f"Command {command_name} not found: {exc}")
        return command

    def _retrieve_callback(self, command_name: str) -> Callable:
        try:
            command = self._callback[command_name]
        except KeyError as exc:
            sys.stderr.write(f"Callback {command_name} not found: {exc}")
        return command
