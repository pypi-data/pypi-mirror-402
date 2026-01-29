from pathlib import Path

from splight_runner.commands.admin import CommandAdmin
from splight_runner.commands.execute_agent import execute_agent
from splight_runner.commands.execute_component import execute_component
from splight_runner.version import __version__

runner = CommandAdmin(name="Splight Runner", version=__version__)


@runner.callback(name="help")
def help() -> None:
    """Prints all the commands"""
    runner.print_commands()


@runner.callback(name="version")
def version() -> None:
    """Splight Runner"""
    print(f"Splight Runner: {__version__}")


@runner.command(name="run-component")
def run_component(file_name: Path, component_id: str) -> None:
    execute_component(component_file=file_name, component_id=component_id)


@runner.command(name="run-agent")
def run_agent() -> None:
    execute_agent()
