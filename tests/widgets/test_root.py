"""Tests for the root :class:`FormWidget` (error-display / copy&paste).

All clipboard-related checks avoid the real OS clipboard (which is not
available in headless/CI sessions on Windows - ``OleSetClipboard`` fails) by
capturing the clipboard-write instead.
"""

import jsonschema
import pytest
from qtpy.QtGui import QClipboard
from qtpy.QtWidgets import QPlainTextEdit


@pytest.fixture
def form(qtbot):
    """A FormWidget wrapping a plain text-widget (the error-box is layout-only)."""
    import pyqtschema.widgets.root as root

    form = root.FormWidget(QPlainTextEdit())
    qtbot.addWidget(form)
    form.show()
    return form


def _error(message, path):
    return jsonschema.ValidationError(message, path=path)


def _capture_clipboard(monkeypatch):
    """Replace the clipboard-write with a recorder (platform-independent)."""
    captured = {}

    def record(self, text, *args, **kwargs):
        captured["text"] = text

    monkeypatch.setattr(QClipboard, "setText", record)
    return captured


def test_error_widget_hidden_by_default(form):
    assert form.error_widget.isHidden()


def test_display_errors_shows_text(form):
    form.display_errors([_error("must be <= 10", ("count",))])

    assert not form.error_widget.isHidden()
    assert form.error_text.toPlainText() == ".count must be <= 10"


def test_display_errors_plain_text_selectable(form):
    """The errors must live in a text-widget so they can be copy&pasted
    (plain QLabel text cannot be selected)."""
    form.display_errors([_error("bad value", ("field",))])

    assert isinstance(form.error_text, QPlainTextEdit)
    assert form.error_text.isReadOnly()
    # selecting + copying the error-text must work (QLabel text cannot be selected)
    form.error_text.selectAll()
    assert form.error_text.textCursor().selectedText() == ".field bad value"


def test_copy_button_copies_all_errors(form, monkeypatch):
    captured = _capture_clipboard(monkeypatch)
    errors = [_error("too small", ("min",)), _error("too big", ("max",))]
    form.display_errors(errors)
    form.copy_button.click()

    assert captured["text"] == ".min too small\n.max too big"


def test_display_errors_int_path(form):
    """Array-index path-components must not crash the display (regression:
    ``'.'.join(err.path)`` used to raise on ``int`` indices)."""
    errors = [_error("must be greater than 0", ("items", 0, "length"))]

    form.display_errors(errors)

    assert form.error_text.toPlainText() == ".items.0.length must be greater than 0"


def test_display_errors_empty_path(form):
    form.display_errors([_error("root-level error", ())])

    assert form.error_text.toPlainText() == "root-level error"


def test_display_errors_without_argument_reshows_previous(form):
    form.display_errors([_error("must be <= 10", ("count",))])
    form.clear_errors()
    assert form.error_widget.isHidden()

    form.display_errors()

    assert not form.error_widget.isHidden()
    # without an explicit error-list nothing new is (re)formatted
    assert form.error_text.toPlainText() == ""


def test_clear_errors_hides_and_clears(form):
    form.display_errors([_error("must be <= 10", ("count",))])
    form.clear_errors()

    assert form.error_widget.isHidden()
    assert form.error_text.toPlainText() == ""
