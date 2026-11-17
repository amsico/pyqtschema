from qtpy.QtWidgets import QLabel

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class NullSchemaWidget(SchemaWidgetMixin, QLabel):
    """Widget for ``{"type": "null"}`` - nothing to edit, the state is always ``None``.

    Appears e.g. as the ``null``-branch of an ``anyOf`` when a schema with
    nullable fields is rendered without :func:`~pyqtschema.schema.normalize_schema`.
    """

    def configure(self):
        self.setText(str(self.schema.get("title") or "None"))
        self.setEnabled(False)

    @state_property
    def state(self) -> None:
        return None

    @state.setter
    def state(self, state) -> None:
        pass
