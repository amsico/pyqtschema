from .builder import WidgetBuilder
from .utils import build_example

VERSION: str = "0.1"


def get_version() -> str:
    """ the current status version """
    return VERSION
