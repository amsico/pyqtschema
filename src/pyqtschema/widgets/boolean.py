from qtpy.QtWidgets import QCheckBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property


class CheckboxSchemaWidget(SchemaWidgetMixin, QCheckBox):
    """Boolean-field checkbox.

    Shows the field's ``title`` as its own label and keeps a standard,
    clearly visible check-indicator.  ``show_title()`` returns ``False`` so
    the surrounding object-form does not add a duplicate label-row for it
    (before, a bare *textless* box was rendered whose checked state was easy
    to miss).
    """

    def show_title(self) -> bool:
        # the checkbox carries its own text - the object-form must not add a
        # separate label for it (which would duplicate the text below).
        return False

    @state_property
    def state(self) -> bool:
        return self.isChecked()

    @state.setter
    def state(self, checked: bool):
        self.setChecked(checked)

    def configure(self):
        self.setText(str(self.schema.get("title") or ""))
        description = self.schema.get("description")
        if description:
            self.setToolTip(str(description))
        self.stateChanged.connect(lambda _: self.on_changed.emit(self.state))
