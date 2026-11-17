"""Read-only handling of schema-widget trees."""
from qtpy.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QAbstractSpinBox,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

#: editor-widget types disabled by :func:`set_widgets_read_only`.
EDITOR_TYPES = (
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QAbstractButton, QAbstractSpinBox, QAbstractItemView,
)


def set_widgets_read_only(root: QWidget, read_only: bool) -> None:
    """Enable/disable all input-widgets below (and including) ``root``.

    A widget implementing ``set_read_only(bool)`` controls its whole subtree
    itself (custom widgets may e.g. keep a table scrollable); every other
    editor widget (see :data:`EDITOR_TYPES`) is simply disabled.
    """
    seen = set()

    def _apply(widget: QWidget, is_root: bool) -> None:
        if id(widget) in seen:
            return
        seen.add(id(widget))
        custom = getattr(widget, "set_read_only", None)
        if callable(custom) and not is_root:
            custom(bool(read_only))
            return
        if isinstance(widget, EDITOR_TYPES) and not _ui_disabled(widget):
            widget.setEnabled(not read_only)
        for child in widget.children():
            if isinstance(child, QWidget):
                _apply(child, False)

    _apply(root, True)


def _ui_disabled(widget: QWidget) -> bool:
    """``ui:disabled`` widgets stay disabled when the form becomes editable."""
    ui_schema = getattr(widget, "ui_schema", None)
    return isinstance(ui_schema, dict) and bool(ui_schema.get("ui:disabled", False))


def apply_read_only(widget: QWidget, read_only: bool) -> None:
    """Make ``widget`` read-only: via its own ``set_read_only`` if it has one,
    otherwise via :func:`set_widgets_read_only`."""
    custom = getattr(widget, "set_read_only", None)
    if callable(custom):
        custom(bool(read_only))
    else:
        set_widgets_read_only(widget, read_only)
