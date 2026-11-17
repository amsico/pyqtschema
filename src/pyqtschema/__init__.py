from .builder import WidgetBuilder
from .schema import normalize_schema, translate_schema
from .registry import SCHEMA_WIDGET_KEY, WidgetRegistry
from .schema_widget import SchemaWidget
from .widgets import CustomObjectWidget
from .utils import build_example
from .__version__ import version


__all__ = [
    "CustomObjectWidget",
    "SCHEMA_WIDGET_KEY",
    "SchemaWidget",
    "WidgetBuilder",
    "WidgetRegistry",
    "build_example",
    "get_version",
    "normalize_schema",
    "translate_schema",
    "version",
]


def get_version() -> str:
    """ the current status version """
    return version
