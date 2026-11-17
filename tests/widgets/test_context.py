"""Tests for the application ``context`` handed from the form to (custom) widgets."""
from qtpy.QtWidgets import QComboBox, QVBoxLayout

from pyqtschema import CustomObjectWidget, SchemaWidget, WidgetBuilder, WidgetRegistry
from pyqtschema.widgets import TextSchemaWidget

SCHEMA = {
    "title": "Apply",
    "type": "object",
    "properties": {
        "run": {"title": "Run", "type": "string", "default": ""},
        "comment": {"title": "Comment", "type": "string", "default": ""},
    },
}


class ChoiceWidget(CustomObjectWidget):
    """Shows ``run`` as a combo filled from ``context["runs"]``, a plain editor without context."""

    def setup_ui(self):
        layout = QVBoxLayout(self)
        runs = (self.context or {}).get("runs")
        if runs:
            self.combo = QComboBox(self)
            self.combo.addItems(runs)
            layout.addWidget(self.combo)
        else:
            self.combo = None
            layout.addWidget(self.build_field("run"))
        layout.addWidget(self.build_field("comment"))


def _registry() -> WidgetRegistry:
    registry = WidgetRegistry()
    registry.register("choice", ChoiceWidget)
    return registry


def test_builder_context_default_none():
    assert WidgetBuilder(SCHEMA).context is None


def test_context_reaches_nested_widgets(qtbot):
    context = {"runs": ["a"]}
    widget = SchemaWidget(SCHEMA, context=context)
    qtbot.addWidget(widget)
    assert widget.context is context
    assert widget.builder.context is context
    assert widget.widget.context is context
    assert isinstance(widget.widget.widgets["run"], TextSchemaWidget)
    assert widget.widget.widgets["run"].context is context


def test_custom_widget_uses_context(qtbot):
    widget = SchemaWidget(SCHEMA, ui_schema={"ui:widget": "choice"}, registry=_registry(),
                          context={"runs": ["r1", "r2"]})
    qtbot.addWidget(widget)
    assert isinstance(widget.widget, ChoiceWidget)
    assert [widget.widget.combo.itemText(i) for i in range(widget.widget.combo.count())] == ["r1", "r2"]


def test_custom_widget_without_context_falls_back(qtbot):
    widget = SchemaWidget(SCHEMA, {"run": "x"}, ui_schema={"ui:widget": "choice"}, registry=_registry())
    qtbot.addWidget(widget)
    assert widget.widget.combo is None
    assert widget.state["run"] == "x"


def test_set_context_rebuilds_keeping_values(qtbot):
    widget = SchemaWidget(SCHEMA, {"comment": "keep"}, ui_schema={"ui:widget": "choice"}, registry=_registry())
    qtbot.addWidget(widget)
    widget.set_context({"runs": ["r1"]})
    assert widget.widget.combo is not None
    assert widget.state["comment"] == "keep"
