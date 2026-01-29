import os

from splight_runner import __file__ as root_file
from splight_runner.api.settings import settings
from splight_runner.logging import log


def execute_agent() -> None:
    """Executes an splight agent after configuring splight runner hooks."""

    root_dir = os.path.dirname(root_file)
    boot_dir = os.path.join(root_dir, "bootstrap")

    python_path = boot_dir
    if "PYTHONPATH" in os.environ:
        all_paths = os.getenv("PYTHONPATH").split(os.path.pathsep)
        if boot_dir not in all_paths:
            all_paths.insert(0, boot_dir)
            python_path = os.path.pathsep.join(all_paths)

    log("Configuring PYTHONPATH env var")
    os.environ["PYTHONPATH"] = python_path
    # The following variable is used for activate hooks
    os.environ["SPLIGHT_RUNNER_ACTIVE"] = "True"

    # Configure env variables for running Splight Agent
    if "SPLIGHT_ACCESS_ID" not in os.environ:
        os.environ["SPLIGHT_ACCESS_ID"] = settings.access_id
    if "SPLIGHT_SECRET_KEY" not in os.environ:
        os.environ["SPLIGHT_SECRET_KEY"] = settings.secret_key
    if "SPLIGHT_PLATFORM_API_HOST" not in os.environ:
        os.environ["SPLIGHT_PLATFORM_API_HOST"] = (
            settings.splight_platform_api_host
        )
    if "COMPUTE_NODE_ID" not in os.environ:
        os.environ["COMPUTE_NODE_ID"] = settings.process_id

    log("Executing Splight Agent")

    command = ["/bin/bash", "-c", "splight-agent"]
    exec_path = "/bin/bash"

    os.execl(exec_path, *command)
