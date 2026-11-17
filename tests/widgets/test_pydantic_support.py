"""Tests for the optional pydantic helpers (:mod:`pyqtschema.pydantic_support`)."""
from typing import List, Optional

import pytest

pydantic = pytest.importorskip("pydantic")
if not pydantic.VERSION.startswith("2"):  # pragma: no cover
    pytest.skip("pyqtschema.pydantic_support requires pydantic v2", allow_module_level=True)

from pydantic import BaseModel, Field, ValidationError  # noqa: E402
from qtpy.QtWidgets import QVBoxLayout  # noqa: E402

from pyqtschema import CustomObjectWidget, SCHEMA_WIDGET_KEY  # noqa: E402
from pyqtschema.pydantic_support import (  # noqa: E402
    ModelWidgetRegistry,
    build_widget,
    iter_models,
    model_schema,
    to_model,
)
from pyqtschema.widgets import ObjectSchemaWidget  # noqa: E402


class Unit(BaseModel):
    value: float = 1.0
    unit: str = "m"


class SpecialUnit(Unit):
    extra: int = 0


class Limits(BaseModel):
    name: str = Field("dummy", title="Name")
    upper: Unit = Unit()
    lower: Optional[Unit] = None
    special: SpecialUnit = SpecialUnit()
    history: List[Unit] = []


class UnitWidget(CustomObjectWidget):
    def setup_ui(self):
        QVBoxLayout(self).addWidget(self.build_field("value"))


def test_iter_models():
    assert set(iter_models(Limits)) == {Limits, Unit, SpecialUnit}


def test_model_schema_markers():
    registry = ModelWidgetRegistry()
    name = registry.register_model(Unit, UnitWidget)
    schema = model_schema(Limits, registry)
    assert schema["$defs"]["Unit"][SCHEMA_WIDGET_KEY] == name
    assert schema["$defs"]["SpecialUnit"][SCHEMA_WIDGET_KEY] == name  # inherited
    assert SCHEMA_WIDGET_KEY not in schema
    assert SCHEMA_WIDGET_KEY not in model_schema(Limits)  # without registry


def test_model_schema_custom_factory():
    schema = model_schema(Limits, schema_factory=lambda m: {"title": m.__name__, "type": "object",
                                                            "properties": {}})
    assert schema["title"] == "Limits"


def test_register_model_requires_known_name():
    registry = ModelWidgetRegistry()
    with pytest.raises(ValueError):
        registry.register_model(Unit, name="missing")
    registry.register("unit", UnitWidget)
    assert registry.register_model(Unit, name="unit") == "unit"


def test_child_registry_model_lookup():
    registry = ModelWidgetRegistry()
    registry.register_model(Unit, UnitWidget, name="unit")
    child = registry.child()
    assert child.model_widget(SpecialUnit) == "unit"
    child.register_model(SpecialUnit, UnitWidget, name="special")
    assert child.model_widget(SpecialUnit) == "special"
    assert registry.model_widget(SpecialUnit) == "unit"


def test_build_widget_from_class(qtbot):
    widget = build_widget(Limits)
    qtbot.addWidget(widget)
    assert widget.state["name"] == "dummy"
    assert isinstance(widget.widget.widgets["upper"], ObjectSchemaWidget)
    assert to_model(widget).upper == Unit()


def test_build_widget_from_instance_and_data(qtbot):
    registry = ModelWidgetRegistry()
    registry.register_model(Unit, UnitWidget)
    widget = build_widget(Limits(name="inst", upper=Unit(value=2, unit="km")),
                          {"upper": {"value": 3}}, registry=registry)
    qtbot.addWidget(widget)
    assert isinstance(widget.widget.widgets["upper"], UnitWidget)
    assert isinstance(widget.widget.widgets["special"], UnitWidget)
    model = to_model(widget)
    assert model.name == "inst"
    assert model.upper == Unit(value=3, unit="km")  # data merged over the instance


def test_to_model_validation_error(qtbot):
    class Coded(BaseModel):
        code: str = Field("ab", min_length=2)

    widget = build_widget(Coded)
    qtbot.addWidget(widget)
    widget.state = {"code": "x"}
    with pytest.raises(ValidationError):
        to_model(widget)
