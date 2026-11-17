from typing import Optional

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property

#: ui-schema keyword: show " (None)" next to a nullable boolean that is None (default: true)
UI_SHOW_NONE = "ui:show_none"


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


class NullableCheckboxSchemaWidget(CheckboxSchemaWidget):
    """Nullable boolean (``Optional[bool]``) as one tristate checkbox.

    Used instead of :class:`~pyqtschema.widgets.NullableSchemaWidget` for
    nullable booleans (a checkbox for ``None`` in front of a checkbox would be
    confusing):

    * checked: ``True``, unchecked: ``False``,
    * partially checked: ``None`` - the start state without a default.

    A click cycles ``None`` -> ``True`` -> ``False`` -> ``None``.

    While the value is ``None``, `` (None)`` is appended to the title - the
    partially checked indicator alone is hard to tell from unchecked in some
    styles.  ui-schema: ``"ui:show_none": false`` hides it.
    """

    #: appended to the title while the value is None
    NONE_SUFFIX = " (None)"

    def configure(self):
        super().configure()
        self._title = self.text()
        self._show_none = bool((self.ui_schema or {}).get(UI_SHOW_NONE, True))
        self.setTristate(True)
        self.stateChanged.connect(lambda _: self._update_text())
        self.setCheckState(Qt.PartiallyChecked)
        self._update_text()
        hint = "partially checked: None"
        description = self.schema.get("description")
        self.setToolTip(f"{description}\n({hint})" if description else hint)

    def _update_text(self) -> None:
        none = self._show_none and self.checkState() == Qt.PartiallyChecked
        self.setText(self._title + self.NONE_SUFFIX if none else self._title)

    # a plain property (no `state_property`): `None` must reach the setter
    @property
    def state(self) -> Optional[bool]:
        check_state = self.checkState()
        if check_state == Qt.PartiallyChecked:
            return None
        return check_state == Qt.Checked

    @state.setter
    def state(self, state: Optional[bool]):
        if state is None:
            self.setCheckState(Qt.PartiallyChecked)
        else:
            self.setCheckState(Qt.Checked if state else Qt.Unchecked)
