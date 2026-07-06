import importlib
import importlib.util
import sys
from pathlib import Path

PACKAGE_NAME = "comfyui_llm_under_test"
ROOT = Path(__file__).resolve().parents[1]


def ensure_package_loaded():
    if PACKAGE_NAME in sys.modules:
        return sys.modules[PACKAGE_NAME]
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)
    return module


def import_module(relative_name):
    ensure_package_loaded()
    return importlib.import_module(f"{PACKAGE_NAME}.{relative_name}")

