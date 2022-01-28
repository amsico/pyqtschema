from functools import wraps
from typing import Tuple

from PyQt5.QtGui import QColor

from .signal import Signal


class StateProperty(property):

    def setter(self, fset):
        @wraps(fset)
        def _setter(*args):
            *head, value = args
            if value is not None:
                fset(*head, value)

        return super().setter(_setter)


state_property = StateProperty


class SchemaWidgetMixin:
    on_changed = Signal()

    VALID_COLOUR = '#ffffff'
    INVALID_COLOUR = '#f6989d'

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'IBuilder', **kwargs):
        super().__init__(**kwargs)

        self.schema = schema
        self.ui_schema = ui_schema
        self.widget_builder = widget_builder

        self.on_changed.connect(lambda _: self.clear_error())

        self._show_title: bool = kwargs.get('show_title', True)
        self.configure()

    def configure(self):
        pass

    def show_title(self) -> bool:
        """ show/hide the title in the form-widget """
        return self._show_title

    @state_property
    def state(self):
        raise NotImplementedError(f"{self.__class__.__name__}.state")

    @state.setter
    def state(self, state):
        raise NotImplementedError(f"{self.__class__.__name__}.state")

    def handle_error(self, path: Tuple[str], err: Exception):
        if path:
            raise ValueError("Cannot handle nested error by default")
        self._set_valid_state(err)

    def clear_error(self):
        self._set_valid_state(None)

    def _set_valid_state(self, error: Exception = None):
        palette = self.palette()
        colour = QColor()
        colour.setNamedColor(self.VALID_COLOUR if error is None else self.INVALID_COLOUR)
        palette.setColor(self.backgroundRole(), colour)

        self.setPalette(palette)
        self.setToolTip("" if error is None else error.message)  # TODO
