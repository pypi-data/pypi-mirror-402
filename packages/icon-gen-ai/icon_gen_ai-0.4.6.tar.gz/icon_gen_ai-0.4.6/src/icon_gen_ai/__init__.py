"""icon-gen-ai: Generate customizable icons from Iconify, URLs, and local files."""

from importlib.metadata import version

__version__ = version("icon-gen-ai")

def _check_deps():
    try:
        import requests
        import urllib3
    except Exception as e:
        raise RuntimeError(
            "Required dependencies could not be imported.\n"
            "Try:\n"
            "  pip install -U requests urllib3\n"
        ) from e

    req_v = tuple(map(int, requests.__version__.split(".")[:2]))
    url_v = tuple(map(int, urllib3.__version__.split(".")[:2]))

    if req_v < (2, 31) and url_v >= (2, 0):
        raise RuntimeError(
            "Incompatible environment detected:\n"
            "requests < 2.31 with urllib3 >= 2.0\n\n"
            "Fix:\n"
            "  pip install -U requests urllib3\n"
        )

_check_deps()

from .generator import IconGenerator

__all__ = ["IconGenerator"]

# AI features (optional)
try:
    from .ai import IconAssistant, is_ai_available, get_available_providers
    __all__.extend(["IconAssistant", "is_ai_available", "get_available_providers"])
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
