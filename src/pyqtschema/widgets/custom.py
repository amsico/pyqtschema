"""Base class for custom widgets of object-schemas."""
from functools import partial
from typing import Any, Dict, Optional, Tuple

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class CustomObjectWidget(SchemaWidgetMixin, QWidget):
    """Base for a custom widget rendering an object-schema.

    Subclasses build their own layout in :meth:`setup_ui` and create the
    editors of single properties with :meth:`build_field` - which uses the
    form's widget-builder, so a property is rendered by its generic widget or
    by another registered custom widget (recursively).

    The base class provides the common plumbing:

    * ``state`` is the object-dict of all built fields; values of properties
      that are *not* built (not shown) are kept and returned unchanged,
    * ``on_changed`` is emitted with the whole state on every field change,
    * validation-errors are routed to the field-widgets by path,
    * no extra title-label is added by the enclosing object-widget.

    Register a subclass directly as factory in a
    :class:`~pyqtschema.registry.WidgetRegistry`.
    """

    on_changed = Signal(object)

    def __init__(self, schema: dict, ui_schema: Optional[dict] = None,
                 widget_builder: Any = None, parent: Optional[QWidget] = None, **kwargs):
        #: property name -> editor widget (filled by `build_field`)
        self.widgets: Dict[str, SchemaWidgetMixin] = {}
        self._values: Dict[str, Any] = {}
        super().__init__(schema, ui_schema or {}, widget_builder, parent=parent, **kwargs)
        self.setup_ui()

    # -- to be implemented ------------------------------------------------
    def setup_ui(self) -> None:
        """Create the layout and the field editors (see :meth:`build_field`)."""

    # -- helpers ----------------------------------------------------------
    @property
    def properties(self) -> Dict[str, dict]:
        """The property-schemas of the object."""
        return self.schema.get("properties", {}) or {}

    def property_title(self, name: str) -> str:
        """The (translated) title of property ``name``."""
        sub = self.widget_builder.schema.resolve_schema(self.properties.get(name, {}))
        return str(sub.get("title") or name)

    def build_field(self, name: str, parent: Optional[QWidget] = None,
                    ui_schema: Optional[dict] = None) -> SchemaWidgetMixin:
        """Create (and track) the editor of property ``name``.

        Args:
            name: property name.
            parent: Qt parent of the editor (default: this widget).
            ui_schema: ui-schema of the property (default: ``self.ui_schema[name]``).
        """
        sub_schema = self.properties[name]
        sub_ui = ui_schema if ui_schema is not None else (self.ui_schema.get(name, {}) or {})
        state = self._values.get(name)
        widget = self.widget_builder.create_widget(sub_schema, sub_ui, state=state,
                                                   parent=parent if parent is not None else self)
        widget.on_changed.connect(partial(self._on_field_changed, name))
        self.widgets[name] = widget
        return widget

    def _on_field_changed(self, name: str, value) -> None:
        self.on_changed.emit(self.state)

    # -- SchemaWidgetMixin ------------------------------------------------
    def show_title(self) -> bool:
        return False

    @state_property
    def state(self) -> dict:
        out = dict(self._values)
        out.update({name: widget.state for name, widget in self.widgets.items()})
        return out

    @state.setter
    def state(self, state: dict):
        for name, value in state.items():
            widget = self.widgets.get(name)
            if widget is not None:
                widget.state = value
            else:
                self._values[name] = value

    def handle_error(self, path: Tuple[str], err: Exception):
        if not path:
            self._set_valid_state(err)
            return
        name, *tail = path
        widget = self.widgets.get(name)
        if widget is not None:
            widget.handle_error(tuple(tail), err)

    def clear_error(self):
        for widget in self.widgets.values():
            widget.clear_error()
