"""Widget for values of any type, edited as JSON."""
import json
from typing import Any, Optional

from qtpy.QtCore import QPoint, Qt
from qtpy.QtGui import QFontDatabase, QPainter
from qtpy.QtWidgets import QPlainTextEdit, QWidget

from pyqtschema.widgets.base import SchemaWidgetMixin


class JsonError(ValueError):
    """A JSON parse error, shaped like a jsonschema error (``message``) for the error display."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _global_pos(event) -> QPoint:
    # Qt6: globalPosition() (QPointF), Qt5: globalPos()
    if hasattr(event, "globalPosition"):
        return event.globalPosition().toPoint()
    return event.globalPos()


class HeightGrip(QWidget):
    """A grip in the bottom-right corner of a text field: dragging it changes the field's height.

    ``QSizeGrip`` cannot be used - it resizes the top-level window, not a
    widget inside a layout.
    """

    SIZE = 12

    def __init__(self, target: QPlainTextEdit, min_height: int):
        super().__init__(target)
        self._target = target
        self._min_height = min_height
        self._start: Optional[QPoint] = None
        self._start_height = 0
        self.setFixedSize(self.SIZE, self.SIZE)
        self.setCursor(Qt.SizeVerCursor)
        self.setToolTip("drag to resize")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().mid().color())
        size = self.SIZE
        for offset in (3, 7, 11):  # three diagonal lines, like a size grip
            painter.drawLine(size - 1, size - offset, size - offset, size - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start = _global_pos(event)
            self._start_height = self._target.height()
            event.accept()

    def _drag_to(self, event) -> None:
        delta = _global_pos(event).y() - self._start.y()
        self._target.setFixedHeight(max(self._min_height, self._start_height + delta))
        self._target.user_resized = True
        event.accept()

    def mouseMoveEvent(self, event):
        if self._start is not None:
            self._drag_to(event)

    def mouseReleaseEvent(self, event):
        # the release position is applied too: not every platform (e.g. offscreen) delivers the move events
        if self._start is not None and event.button() == Qt.LeftButton:
            self._drag_to(event)
            self._start = None


class JsonSchemaWidget(SchemaWidgetMixin, QPlainTextEdit):
    """A value of any type as JSON text (``42``, ``"text"``, ``[1, 2]``, ``{"a": 1}``, ``null``).

    Default widget of nodes the schema does not restrict to a type - ``Any``
    in pydantic (``{}``) - and of objects without ``properties``
    (``Dict[str, Any]``).  Selectable for every type with ``"ui:widget": "json"``.

    A multi-line field with a monospace font; lists and objects are shown
    indented.  The height fits the content (2 to 12 lines) and can be changed
    with the mouse by dragging the grip in the bottom-right corner.  Tab moves
    the focus to the next field.

    The input is parsed strictly: invalid JSON marks the field (the parse
    error is shown as tooltip) and the state keeps the last valid value -
    nothing is silently reinterpreted (``hello`` is not taken as ``"hello"``).
    An empty field is ``null``.
    """

    #: rows of the initial height: fitted to the content within these limits
    MIN_ROWS = 2
    MAX_ROWS = 12

    def configure(self):
        self._value: Any = None
        self._updating = False
        #: the height was changed with the grip - no automatic fitting anymore
        self.user_resized = False
        self.setPlaceholderText('JSON, e.g. 42, "text", [1, 2], {"key": 1}, null')
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setTabChangesFocus(True)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        description = self.schema.get("description")
        if description:
            self.setToolTip(str(description))
        self.grip = HeightGrip(self, min_height=self._height_for_rows(1))
        self.textChanged.connect(self._on_text_changed)
        self._fit_height()

    # a plain property (no `state_property`): `None` is the JSON value null
    @property
    def state(self) -> Any:
        return self._value

    @state.setter
    def state(self, state: Any):
        self._value = state
        self._updating = True
        try:
            self.setPlainText(self.format(state))
        finally:
            self._updating = False
        self.clear_error()
        self._fit_height()

    @staticmethod
    def format(value: Any) -> str:
        """The text of a value: empty for null, lists/objects indented."""
        if value is None:
            return ""
        if isinstance(value, (list, dict)) and value:
            return json.dumps(value, indent=2, ensure_ascii=False)
        return json.dumps(value, ensure_ascii=False)

    def is_valid_json(self) -> bool:
        """Whether the current text is valid JSON (i.e. ``state`` matches the text)."""
        try:
            self._parse(self.toPlainText())
        except JsonError:
            return False
        return True

    @staticmethod
    def _parse(text: str) -> Any:
        if not text.strip():
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError as err:
            raise JsonError(f"invalid JSON: {err.msg} (line {err.lineno}, column {err.colno})") from err

    def _on_text_changed(self) -> None:
        if self._updating:
            return
        try:
            value = self._parse(self.toPlainText())
        except JsonError as err:
            self._set_valid_state(err)
            return
        self._value = value
        self.on_changed.emit(value)

    def _height_for_rows(self, rows: int) -> int:
        margins = self.contentsMargins()
        document_margin = int(self.document().documentMargin())
        return (rows * self.fontMetrics().lineSpacing() + 2 * document_margin
                + margins.top() + margins.bottom() + 2)

    def _fit_height(self) -> None:
        if self.user_resized:
            return
        lines = self.toPlainText().count("\n") + 1
        rows = min(self.MAX_ROWS, max(self.MIN_ROWS, lines))
        self.setFixedHeight(self._height_for_rows(rows))

    def showEvent(self, event):
        # the style may change the frame when the widget is polished in its
        # final hierarchy - fit again, so no scroll bar appears for content that fits
        super().showEvent(event)
        self._fit_height()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # keep the grip in the bottom-right corner (inside the frame)
        frame = self.frameWidth()
        self.grip.move(self.width() - self.grip.width() - frame, self.height() - self.grip.height() - frame)
        self.grip.raise_()
