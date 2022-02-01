from .builder import WidgetBuilder
from .utils import build_example
from .__version__ import version


def get_version() -> str:
    """ the current status version """
    return version
