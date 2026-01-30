import os
from dataclasses import dataclass, field
from functools import partial
from typing import List

SECRET_DIR = "/etc/config"


class MissingEnvVariable(Exception): ...


def load_variable(var_name: str, default: str | None = None) -> str:
    secret_file = os.path.join(SECRET_DIR, var_name)
    if os.path.exists(secret_file):
        with open(secret_file) as f:
            variable = f.read().strip()
    elif os.getenv(var_name):
        variable = os.getenv(var_name)
    elif default:
        variable = default
    else:
        raise MissingEnvVariable(f"{var_name} is missing")
    return variable


def load_multiple_variable(var_names: List[str]) -> str:
    value = None
    for var_name in var_names:
        try:
            value = load_variable(var_name)
            break
        except MissingEnvVariable:
            continue

    if value is None:
        raise MissingEnvVariable(f"On of {var_names} is missing")
    return value


@dataclass
class SplightSettings:
    """Class for holding Splight Runner settings."""

    access_id: str = field(
        default_factory=partial(load_variable, "SPLIGHT_ACCESS_ID")
    )
    secret_key: str = field(
        default_factory=partial(load_variable, "SPLIGHT_SECRET_KEY")
    )
    splight_platform_api_host: str = field(
        default_factory=partial(load_variable, "SPLIGHT_PLATFORM_API_HOST")
    )
    process_id: str = field(
        default_factory=partial(
            load_multiple_variable,
            ["COMPONENT_ID", "COMPUTE_NODE_ID", "AGENT_ID"],
        )
    )
    process_type: str = field(
        default_factory=partial(load_variable, "PROCESS_TYPE")
    )
    api_version: str = field(
        default_factory=partial(load_variable, "API_VERSION", default="v3")
    )


settings = SplightSettings()
