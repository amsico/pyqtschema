"""Widget for nullable fields (``Optional`` in pydantic)."""
from typing import TYPE_CHECKING, Any, Tuple

from qtpy.QtWidgets import QCheckBox, QHBoxLayout, QWidget

from pyqtschema.schema import nullable_inner
from pyqtschema.widgets.base import SchemaWidgetMixin

if TYPE_CHECKING:  # pragma: no cover
    from pyqtschema.builder import WidgetBuilder


class NullableSchemaWidget(SchemaWidgetMixin, QWidget):
    """A checkbox for ``None`` in front of the widget of the editable part.

    Built for every node marked ``x-nullable`` by
    :func:`~pyqtschema.schema.normalize_schema` - e.g. ``my_int: int | None``:

    * unchecked: the state is ``None``, the inner widget is disabled,
    * checked: the state is the value of the inner widget.

    The inner widget is created by the widget-builder from
    :func:`~pyqtschema.schema.nullable_inner` with the same ui-schema, so
    ``ui:*``-options, ``x-widget`` and ``$ref``-registrations of the
    :class:`~pyqtschema.registry.WidgetRegistry` apply to it.  Without a
    ``default`` (or with ``default: null``) the field starts unchecked.
    """

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        self.check = QCheckBox()
        # the inner widget sits in a plain container: disabling the container
        # keeps it disabled while unchecked, even if the read-only handling
        # (re-)enables the editors inside
        self.body = QWidget()
        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

        self.inner: SchemaWidgetMixin = widget_builder.create_widget(
            nullable_inner(schema), ui_schema, parent=self.body)
        body_layout = QHBoxLayout(self.body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(self.inner)
        self.inner.on_changed.connect(self._on_inner_changed)
        self._set_checked(False)

    def configure(self):
        self.check.setToolTip("set a value (unchecked: None)")
        self.check.toggled.connect(self._on_toggled)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check, 0)
        layout.addWidget(self.body, 1)

    def show_title(self) -> bool:
        return self.inner.show_title()

    # `state` is a plain property (no `state_property`): `None` must reach the
    # setter - it is the value "unchecked", not "nothing to set".
    @property
    def state(self) -> Any:
        return self.inner.state if self.check.isChecked() else None

    @state.setter
    def state(self, state: Any):
        if state is None:
            self._set_checked(False)
            return
        self.inner.state = state
        self._set_checked(True)

    def is_null(self) -> bool:
        return not self.check.isChecked()

    def _set_checked(self, checked: bool) -> None:
        changed = self.check.isChecked() != checked
        self.check.setChecked(checked)  # emits via `_on_toggled` if changed
        if not changed:
            self.body.setEnabled(checked)

    def _on_toggled(self, checked: bool) -> None:
        self.body.setEnabled(checked)
        self.on_changed.emit(self.state)

    def _on_inner_changed(self, _value) -> None:
        if self.check.isChecked():
            self.on_changed.emit(self.state)

    def handle_error(self, path: Tuple[str], err: Exception):
        self.inner.handle_error(path, err)

    def clear_error(self):
        # also called by the mixin before `inner` exists
        inner = getattr(self, "inner", None)
        if inner is not None:
            inner.clear_error()
