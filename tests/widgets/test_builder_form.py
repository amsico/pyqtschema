"""`WidgetBuilder.create_form` and `SchemaWidget` share one form-/validation-path."""
from pyqtschema import SchemaWidget, WidgetBuilder, WidgetRegistry
from pyqtschema.widgets import AnyOfSchemaWidget, FormWidget, NullSchemaWidget

from .test_schema_widget import SCHEMA, UnitWidget

STRING_SCHEMA = {"type": "object", "properties": {"n": {"type": "string", "minLength": 3, "default": "abcd"}}}


def test_create_form_applies_registry_paths(qtbot):
    registry = WidgetRegistry()
    registry.register("unit", UnitWidget, path="upper")
    # the builder does not normalize: drop the nullable `lower` (anyOf with null)
    schema = {**SCHEMA, "properties": {k: v for k, v in SCHEMA["properties"].items() if k != "lower"}}
    form = WidgetBuilder(schema, registry=registry).create_form()
    qtbot.addWidget(form)
    assert isinstance(form.widget.widgets["upper"], UnitWidget)


def test_create_form_live_validation(qtbot):
    form = WidgetBuilder(STRING_SCHEMA).create_form()
    qtbot.addWidget(form)
    form.widget.widgets["n"].setText("a")
    assert not form.error_widget.isHidden()
    assert form.widget.widgets["n"].toolTip()


def test_create_form_without_live_validation(qtbot):
    form = WidgetBuilder(STRING_SCHEMA).create_form(validate=False)
    qtbot.addWidget(form)
    assert isinstance(form, FormWidget)
    form.widget.widgets["n"].setText("a")
    assert form.error_widget.isHidden()
    # explicit validation still works
    assert [list(e.path) for e in form.validate()] == [["n"]]
    assert not form.error_widget.isHidden()


def test_show_errors_marks_fields(qtbot):
    widget = SchemaWidget(STRING_SCHEMA, validate=False)
    qtbot.addWidget(widget)
    widget.state = {"n": "a"}
    assert widget.form.error_widget.isHidden()
    assert not widget.show_errors()
    assert not widget.form.error_widget.isHidden()
    assert widget.widget.widgets["n"].toolTip()
    widget.state = {"n": "abcd"}
    assert widget.show_errors()
    assert widget.form.error_widget.isHidden()


def test_builder_renders_null_branch_without_normalization(qtbot):
    # previously: KeyError 'null' - the raw builder shows the null-branch as a choice
    form = WidgetBuilder(SCHEMA).create_form()
    qtbot.addWidget(form)
    lower = form.widget.widgets["lower"]
    assert isinstance(lower, AnyOfSchemaWidget)
    assert isinstance(lower.widgets[1], NullSchemaWidget)
    lower.select_combo.setCurrentIndex(1)
    assert form.widget.state["lower"] is None
    assert not form.validate()
