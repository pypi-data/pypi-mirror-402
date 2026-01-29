import importlib.util
import os
import sys
_pkg_dir = os.path.dirname(__file__)
_so_path = os.path.join(_pkg_dir, "Devil.so")
if os.path.exists(_so_path):
    spec = importlib.util.spec_from_file_location("Devil", _so_path)
    Devil = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(Devil)
    globals().update(Devil.__dict__)
else:
    raise ImportError("Devil.so not found")