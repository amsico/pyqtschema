from functools import wraps
from typing import TYPE_CHECKING, Tuple

from qtpy.QtCore import Signal

if TYPE_CHECKING:  # pragma: no cover
    from pyqtschema.builder import IBuilder


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
    on_changed = Signal(object)

    #: border colour of a field with a validation error
    INVALID_COLOUR = '#d32f2f'
    #: dynamic property set on a field with a validation error (``*[schemaInvalid="true"]``)
    INVALID_PROPERTY = 'schemaInvalid'
    #: separates the error rule from a style sheet the widget sets itself
    _INVALID_MARKER = '/* pyqtschema: invalid */'

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

    @property
    def context(self):
        """The application context of the form (``WidgetBuilder.context``) or None.

        Custom widgets use it to reach application data (e.g. the choices of a combo box) without a
        dependency of pyqtschema on that data; without a context they should fall back to plain editing.
        """
        return getattr(self.widget_builder, 'context', None)

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
        """Mark the field with a red border (and the message as tooltip) or unmark it.

        A style sheet is used instead of the palette: styles like ``windows11``
        ignore the palette of input fields.  The rule only matches the widget
        itself (by the dynamic property), not its children; a style sheet the
        widget sets itself is kept.
        """
        own_sheet = self.styleSheet().split(self._INVALID_MARKER)[0].rstrip()
        self.setProperty(self.INVALID_PROPERTY, error is not None)
        if error is None:
            self.setStyleSheet(own_sheet)
        else:
            rule = f'*[{self.INVALID_PROPERTY}="true"] {{ border: 1px solid {self.INVALID_COLOUR}; }}'
            self.setStyleSheet(f"{own_sheet}\n{self._INVALID_MARKER}\n{rule}".lstrip())
        self.setToolTip("" if error is None else getattr(error, "message", str(error)))

    def is_marked_invalid(self) -> bool:
        """Whether the field is marked with a validation error."""
        return bool(self.property(self.INVALID_PROPERTY))
