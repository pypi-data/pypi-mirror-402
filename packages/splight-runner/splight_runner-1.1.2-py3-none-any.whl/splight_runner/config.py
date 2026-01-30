import logging
from types import ModuleType

try:
    import splight_lib

    SPL_LIB_INSTALLED = True
except Exception as exc:
    print("Error importing splight_lib", exc)
    SPL_LIB_INSTALLED = False

from splight_runner.hooks import copy_module, on_import, reload_module
from splight_runner.logging import log
from splight_runner.wrapper.healthcheck import healthcheck_wrapper
from splight_runner.wrapper.hooks import finish_execution
from splight_runner.wrapper.logging import call_handlers_wrapper


@on_import("logging")
def on_logging_import(module: ModuleType) -> ModuleType:
    """Hook for modifying default behavior for the logging module.

    Parameters
    ----------
    module: ModuleType
        The built-in logging module

    Returns
    -------
    ModuleType: The logging module updated
    """
    original = getattr(module.Logger, "callHandlers", None)
    if original:
        wrapped = call_handlers_wrapper(original)
        new_module = copy_module(logging)
        setattr(new_module.Logger, "callHandlers", wrapped)
        return new_module
    return module


@on_import("splight_lib")
def on_splight_lib_import(module: ModuleType) -> ModuleType:
    if hasattr(module.execution, "ExecutionClient"):
        original = getattr(
            module.execution.ExecutionClient, "healthcheck", None
        )
        engine_name = "ExecutionClient"
    elif hasattr(module.execution, "ExecutionEngine"):
        original = getattr(
            module.execution.ExecutionEngine, "healthcheck", None
        )
        engine_name = "ExecutionEngine"
    else:
        log("Unable to find Execution Engine in splight_lib")
        return module
    if original and SPL_LIB_INSTALLED:
        wrapped = healthcheck_wrapper(original)
        new_module = copy_module(splight_lib)
        engine = getattr(module.execution, engine_name)
        setattr(engine, "healthcheck", wrapped)
        return new_module
    return module


# Reload logging module to update everywhere
reload_module(logging)


if SPL_LIB_INSTALLED:
    reload_module(splight_lib)

finish_execution()
