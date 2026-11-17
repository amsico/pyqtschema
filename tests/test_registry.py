"""Tests for the (Qt-free) :class:`WidgetRegistry`."""
import pytest

from pyqtschema.registry import SCHEMA_WIDGET_KEY, UI_WIDGET_KEY, WidgetRegistry, ref_name


def factory_a(*args, **kwargs):
    return "a"


def factory_b(*args, **kwargs):
    return "b"


def test_ref_name():
    assert ref_name("#/$defs/Unit") == "Unit"
    assert ref_name("#/definitions/Unit") == "Unit"
    assert ref_name(None) is None


def test_register_duplicate_name_raises():
    registry = WidgetRegistry()
    registry.register("a", factory_a)
    with pytest.raises(ValueError):
        registry.register("a", factory_b)
    registry.register("a", factory_b, replace=True)
    assert registry.factory("a") is factory_b


def test_register_requires_callable():
    with pytest.raises(TypeError):
        WidgetRegistry().register("a", "no-factory")


def test_resolve_order():
    registry = WidgetRegistry()
    registry.register("a", factory_a, ref="Unit")
    registry.register("b", factory_b)

    # nothing matches -> generic widget
    assert registry.resolve({"type": "object"}, {}) is None
    # ref name
    assert registry.resolve({"type": "object"}, {}, ref="#/$defs/Unit") is factory_a
    # schema marker wins over the ref
    assert registry.resolve({SCHEMA_WIDGET_KEY: "b"}, {}, ref="#/$defs/Unit") is factory_b
    # ui:widget wins over the schema marker
    assert registry.resolve({SCHEMA_WIDGET_KEY: "b"}, {UI_WIDGET_KEY: "a"}) is factory_a
    # unknown ui:widget (a builtin variant like "textarea") is ignored
    assert registry.resolve({SCHEMA_WIDGET_KEY: "b"}, {UI_WIDGET_KEY: "textarea"}) is factory_b


def test_apply_paths_merges_ui_schema():
    registry = WidgetRegistry()
    registry.register("a", factory_a, path=["upper", "items.items.unit"])
    ui = registry.apply_paths({"upper": {"ui:hidden": True}, "lower": {UI_WIDGET_KEY: "x"}})
    assert ui["upper"] == {"ui:hidden": True, UI_WIDGET_KEY: "a"}
    assert ui["items"]["items"]["unit"] == {UI_WIDGET_KEY: "a"}
    assert ui["lower"] == {UI_WIDGET_KEY: "x"}


def test_apply_paths_keeps_explicit_widget():
    registry = WidgetRegistry()
    registry.register("a", factory_a, path="upper")
    original = {"upper": {UI_WIDGET_KEY: "b"}}
    assert registry.apply_paths(original)["upper"][UI_WIDGET_KEY] == "b"
    assert original == {"upper": {UI_WIDGET_KEY: "b"}}  # not modified


def test_child_layers():
    parent = WidgetRegistry()
    parent.register("a", factory_a, ref="Unit", path="x")
    child = parent.child()
    child.register("b", factory_b)
    child.register_ref("Unit", "b")

    assert child.resolve({}, {}, ref="#/$defs/Unit") is factory_b
    assert parent.resolve({}, {}, ref="#/$defs/Unit") is factory_a
    assert child.factory("a") is factory_a
    assert not parent.has("b")
    assert set(child.names()) == {"a", "b"}
    assert child.paths() == {("x",): "a"}
