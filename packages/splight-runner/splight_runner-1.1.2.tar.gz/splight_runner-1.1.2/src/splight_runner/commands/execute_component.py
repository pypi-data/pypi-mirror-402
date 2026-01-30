import os
import sys
from pathlib import Path

from splight_runner import __file__ as root_file
from splight_runner.api.settings import settings


class InvalidComponentLanguage(Exception): ...


class ComponentDoesNotExists(Exception): ...


def execute_component(component_file: Path, component_id: str) -> None:
    """Executes a component after configuring splight runner hooks.

    Parameters
    ----------
    component_file: Path
        The path to the main file for the component.
    component_id: str
        The ID for the component to be executed.

    Returns
    -------
    None

    Raises
    ------
    ComponentDoesNotExists
        If the component file does not exists.
    InvalidComponentLanguage
        If the component is written in a non-supported language.
    """
    # TODO: Add some logs messages for debugging
    main_file = component_file.name
    component_path = component_file.parent.resolve()
    if not component_file.exists():
        raise ComponentDoesNotExists("Component does not exists")
    if main_file.endswith(".py"):
        base_cmd = "python3"
    else:
        raise InvalidComponentLanguage(
            "Component is not written in a supported language"
        )

    root_dir = os.path.dirname(root_file)
    boot_dir = os.path.join(root_dir, "bootstrap")

    python_path = boot_dir
    if "PYTHONPATH" in os.environ:
        all_paths = os.getenv("PYTHONPATH").split(os.path.pathsep)
        if boot_dir not in all_paths:
            all_paths.insert(0, boot_dir)
            python_path = os.path.pathsep.join(all_paths)

    os.environ["PYTHONPATH"] = python_path
    # The following variable is used for activate hooks
    os.environ["SPLIGHT_RUNNER_ACTIVE"] = "True"

    # TODO: improve how env variables are configured
    if "SPLIGHT_ACCESS_ID" not in os.environ:
        os.environ["SPLIGHT_ACCESS_ID"] = settings.access_id
    if "SPLIGHT_SECRET_KEY" not in os.environ:
        os.environ["SPLIGHT_SECRET_KEY"] = settings.secret_key
    if "SPLIGHT_PLATFORM_API_HOST" not in os.environ:
        os.environ["SPLIGHT_PLATFORM_API_HOST"] = (
            settings.splight_platform_api_host
        )
    if "COMPONENT_ID" not in os.environ:
        os.environ["COMPONENT_ID"] = settings.process_id

    os.chdir(component_path)
    exec_path = sys.executable
    command = [
        base_cmd,
        main_file,
        "--component-id",
        component_id,
    ]
    os.execl(exec_path, *command)
