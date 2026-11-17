from typing import Any, Dict, List, Optional

from qtpy.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyqtschema.widgets.base import SchemaWidgetMixin


class FormWidget(QWidget):
    """Root widget: the schema-widget plus an error display.

    Args:
        widget: the root schema-widget.
        validator: jsonschema validator used by :meth:`validate` (optional).
        live_validation: validate on every change of ``widget`` (requires
            ``validator``).
    """

    def __init__(self, widget: SchemaWidgetMixin, *args, validator=None,
                 live_validation: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.validator = validator
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.error_widget = QGroupBox(parent=self)
        self.error_widget.setTitle("Errors")
        self.error_layout = QVBoxLayout()
        self.error_widget.setLayout(self.error_layout)
        self.error_widget.hide()

        # read-only text-widget: the model-errors are visible *and* selectable,
        # so they can be copy&pasted (plain QLabel text cannot be selected).
        self.error_text = QPlainTextEdit(parent=self.error_widget)
        self.error_text.setReadOnly(True)
        self.error_layout.addWidget(self.error_text)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.copy_button = QPushButton("Copy", parent=self.error_widget)
        self.copy_button.setToolTip("Copy all errors to the clipboard")
        self.copy_button.clicked.connect(self._copy_errors)
        buttons.addWidget(self.copy_button)
        self.error_layout.addLayout(buttons)

        layout.addWidget(self.error_widget)
        layout.addWidget(widget)

        self.widget = widget
        if live_validation:
            if validator is None:
                raise ValueError("live_validation requires a validator")
            widget.on_changed.connect(self.validate)

    def validate(self, data: Any = None) -> List[Exception]:
        """Validate ``data`` (default: the current state) and show the errors.

        Shows the error list and routes every error to the affected field
        (``handle_error``).  Returns the errors (empty if valid).
        """
        if self.validator is None:
            raise RuntimeError("FormWidget has no validator")
        if data is None:
            data = self.widget.state
        self.clear_errors()
        errors = [*self.validator.iter_errors(data)]
        if errors:
            self.display_errors(errors)
        for err in errors:
            self.widget.handle_error(err.path, err)
        return errors

    def display_errors(self, errors: Optional[List[Exception]] = None):
        """Show the given validation-errors (or re-show the previous ones).

        ``errors`` is optional so callers can simply re-surface the errors
        that are already on display.
        """
        self.error_widget.show()
        if errors is not None:
            self.error_text.setPlainText(self._format_errors(errors))

    def clear_errors(self):
        self.error_widget.hide()
        self.error_text.clear()

    def _copy_errors(self):
        """Copy all validation-errors to the clipboard as plain text."""
        QApplication.clipboard().setText(self.error_text.toPlainText())

    @staticmethod
    def _format_errors(errors: List[Exception]) -> str:
        """Format validation-errors as plain text (one line per error)."""
        lines = []
        for err in errors:
            path = '.'.join(str(p) for p in err.path)
            prefix = f'.{path} ' if path else ''
            lines.append(f"{prefix}{getattr(err, 'message', err)}")
        return '\n'.join(lines)

    @property
    def state(self) -> Dict:
        return self.widget.state

    @state.setter
    def state(self, state: dict):
        self.widget.state = state
