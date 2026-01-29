import importlib

__all__ = ["analysis", "processing", "plotting", "parsing", "utils", "resources"]

# Lazy loading of the submodules
def __getattr__(name):
    if name in __all__:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")