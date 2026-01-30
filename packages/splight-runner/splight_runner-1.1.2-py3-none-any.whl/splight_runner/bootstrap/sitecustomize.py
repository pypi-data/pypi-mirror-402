# This file is used for configuring splight runner in runtime. In particular
# loads some env vars and activate hooks for sending logs.
# All hooks or configurations for the Splight Runner should be loaded in
# this file.

import ast
import os
import sys

runner_active = ast.literal_eval(os.getenv("SPLIGHT_RUNNER_ACTIVE", "False"))

boot_directory = os.path.dirname(__file__)
root_directory = os.path.dirname(os.path.dirname(boot_directory))

path = list(sys.path)

if boot_directory in path:
    del path[path.index(boot_directory)]

try:
    from importlib.machinery import PathFinder

    module_spec = PathFinder.find_spec("sitecustomize", path=path)
except ImportError as exc:
    sys.stdout.write("Unable to import Splight Runner sitecustomie", exc)
    sys.stdout.flush()
else:
    if module_spec is not None:
        module_spec.loader.load_module("sitecustomize")

if runner_active:
    do_insert = root_directory not in sys.path
    if do_insert:
        sys.path.insert(0, root_directory)

    import splight_runner.config

    if do_insert:
        del sys.path[sys.path.index(root_directory)]
