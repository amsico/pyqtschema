import pytest

from pyqtschema.widgets import SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget
from pyqtschema.widgets.numeric import float_range_from_schema, int_range_from_schema


def schema_for(cls):
    # a slider cannot be created without boundary conditions
    if cls is IntegerRangeSchemaWidget:
        return {"minimum": 0, "maximum": 10}
    return {}


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget])
def test_text_init(cls, builder, qtbot):
    schema = schema_for(cls)
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget])
def test_text_state_write_int(cls, builder, qtbot):
    schema = schema_for(cls)
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)

    value = 6
    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget.state = value
    assert widget.value() == value


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget, IntegerRangeSchemaWidget])
def test_text_state_read_int(cls, builder, qtbot):
    schema = schema_for(cls)
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)

    value = 6
    with qtbot.waitSignal(widget.valueChanged, timeout=1000):
        widget.setValue(value)
    assert widget.state == value


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget])
def test_zero_bounds_respected(cls, builder, qtbot):
    """min/max = 0 must be honored (`if maximum:` treated 0 as falsy)."""
    schema = {"minimum": 0, "maximum": 0}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)
    assert widget.maximum() == 0
    assert widget.minimum() == 0


@pytest.mark.parametrize('cls, maximum', [(SpinSchemaWidget, 2 ** 31 - 1),
                                          (SpinDoubleSchemaWidget, float('inf'))])
def test_default_max_when_unbounded(cls, maximum, builder, qtbot):
    schema = {}
    widget = cls(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)
    assert widget.maximum() == maximum


def test_slider_multiple_of(builder, qtbot):
    """``multipleOf`` drives tick interval/step (also works on PySide6)."""
    schema = {"minimum": 0, "maximum": 10, "multipleOf": 2}
    widget = IntegerRangeSchemaWidget(schema, {}, builder)
    widget.show()
    qtbot.addWidget(widget)
    assert widget.tickInterval() == 2
    assert widget.singleStep() == 2


@pytest.mark.parametrize('cls, minimum', [(SpinSchemaWidget, -2 ** 31),
                                          (SpinDoubleSchemaWidget, float('-inf'))])
def test_default_min_when_unbounded(cls, minimum, builder, qtbot):
    """without `minimum` negative values must be possible (Qt-default is 0)."""
    widget = cls({}, {}, builder)
    qtbot.addWidget(widget)
    assert widget.minimum() == minimum


@pytest.mark.parametrize('value', [2 ** 31 - 1, -2 ** 31, 1_500_000_000])
def test_int_full_range_unbounded(value, builder, qtbot):
    """the whole 32-bit range of the QSpinBox is usable without bounds."""
    widget = SpinSchemaWidget({}, {}, builder)
    qtbot.addWidget(widget)
    widget.state = value
    assert widget.state == value


def test_float_large_values_unbounded(builder, qtbot):
    widget = SpinDoubleSchemaWidget({}, {}, builder)
    qtbot.addWidget(widget)
    widget.state = 1e12
    assert widget.state == 1e12
    widget.state = -1e12
    assert widget.state == -1e12


def test_int_schema_bounds_beyond_32_bit_are_clamped(builder, qtbot, caplog):
    """schema-bounds outside the QSpinBox range must not raise (OverflowError)."""
    widget = SpinSchemaWidget({"minimum": -10 ** 12, "maximum": 10 ** 12}, {}, builder)
    qtbot.addWidget(widget)
    assert widget.minimum() == -2 ** 31
    assert widget.maximum() == 2 ** 31 - 1
    assert "exceeds the 32-bit range" in caplog.text


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget])
def test_negative_state_unbounded(cls, builder, qtbot):
    widget = cls({}, {}, builder)
    qtbot.addWidget(widget)
    widget.state = -5
    assert widget.state == -5


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget])
def test_minimum_still_clamps(cls, builder, qtbot):
    widget = cls({"minimum": 0}, {}, builder)
    qtbot.addWidget(widget)
    widget.state = -5
    assert widget.state == 0


@pytest.mark.parametrize('schema_type', ["integer", "number"])
def test_schema_widget_negative_data(schema_type, qtbot):
    """`SchemaWidget(schema, data)` keeps a negative value (was clamped to 0)."""
    from pyqtschema import SchemaWidget

    schema = {"type": "object", "properties": {"x": {"type": schema_type}}}
    widget = SchemaWidget(schema, data={"x": -5})
    qtbot.addWidget(widget)
    assert widget.state == {"x": -5}


@pytest.mark.parametrize('schema, expected', [
    ({}, (None, None)),
    ({"minimum": 2, "maximum": 10}, (2, 10)),                    # ge / le
    ({"exclusiveMinimum": 2, "exclusiveMaximum": 10}, (3, 9)),   # gt / lt
    ({"exclusiveMinimum": 2.5, "exclusiveMaximum": 9.5}, (3, 9)),
    ({"minimum": 2.5, "maximum": 9.5}, (3, 9)),
    ({"minimum": 2, "exclusiveMinimum": 2}, (3, None)),          # stricter wins
    ({"minimum": 5, "exclusiveMinimum": 2}, (5, None)),
    ({"maximum": 5, "exclusiveMaximum": 10}, (None, 5)),
    ({"minimum": 2, "exclusiveMinimum": True,                     # draft 4
      "maximum": 10, "exclusiveMaximum": False}, (3, 10)),
    ({"exclusiveMinimum": True}, (None, None)),                   # draft 4 w/o minimum
])
def test_int_range_from_schema(schema, expected):
    assert int_range_from_schema(schema) == expected


@pytest.mark.parametrize('schema, expected', [
    ({"minimum": 0.5, "maximum": 10}, (0.5, 10)),
    ({"exclusiveMinimum": 0, "exclusiveMaximum": 10}, (0.01, 9.99)),
    ({"minimum": 0, "exclusiveMinimum": True}, (0.01, None)),
])
def test_float_range_from_schema(schema, expected):
    assert float_range_from_schema(schema, 0.01) == pytest.approx(expected)


def test_spin_exclusive_bounds(builder, qtbot):
    """gt=2 / lt=10: the bounds themselves are not selectable."""
    widget = SpinSchemaWidget({"exclusiveMinimum": 2, "exclusiveMaximum": 10}, {}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (3, 9)
    widget.state = 2
    assert widget.state == 3


@pytest.mark.parametrize('schema, expected', [
    ({"exclusiveMinimum": 0}, 0.01),                      # smallest displayable step
    ({"exclusiveMinimum": 0, "multipleOf": 0.5}, 0.5),    # one step of multipleOf
])
def test_double_spin_exclusive_minimum(schema, expected, builder, qtbot):
    widget = SpinDoubleSchemaWidget(schema, {}, builder)
    qtbot.addWidget(widget)
    assert widget.minimum() == pytest.approx(expected)


def test_slider_exclusive_bounds(builder, qtbot):
    widget = IntegerRangeSchemaWidget({"exclusiveMinimum": 0, "exclusiveMaximum": 10}, {}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (1, 9)


def test_pydantic_gt_lt_is_valid(qtbot):
    """clamping to the bounds of `gt`/`lt` yields a valid state (was: the bound itself)."""
    pydantic = pytest.importorskip("pydantic")
    from pyqtschema import SchemaWidget

    class M(pydantic.BaseModel):
        a: int = pydantic.Field(5, gt=2, lt=10)
        b: float = pydantic.Field(5.0, gt=0)

    widget = SchemaWidget(M.model_json_schema())
    qtbot.addWidget(widget)
    widget.state = {"a": 0, "b": -1}
    assert widget.state["a"] == 3
    assert widget.state["b"] > 0
    assert widget.is_valid()
    widget.state = {"a": 100, "b": 1.0}
    assert widget.state["a"] == 9
    assert widget.is_valid()


# --- ui-schema: ui:min, ui:max, ui:step, ui:decimals -----------------------

@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget])
def test_ui_min_max_without_schema_bounds(cls, builder, qtbot, caplog):
    widget = cls({}, {"ui:min": -5, "ui:max": 50}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (-5, 50)
    assert not caplog.records


@pytest.mark.parametrize('cls', [SpinSchemaWidget, SpinDoubleSchemaWidget])
def test_ui_min_max_schema_wins(cls, builder, qtbot, caplog):
    """a conflicting ui:min/ui:max is ignored: the schema-bound wins (warning)."""
    widget = cls({"minimum": 0, "maximum": 10}, {"ui:min": -5, "ui:max": 50}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (0, 10)
    assert "ui:min -5" in caplog.text
    assert "ui:max 50" in caplog.text


def test_ui_min_equal_to_schema_no_warning(builder, qtbot, caplog):
    widget = SpinSchemaWidget({"exclusiveMinimum": 2}, {"ui:min": 3}, builder)
    qtbot.addWidget(widget)
    assert widget.minimum() == 3
    assert not caplog.records


def test_ui_min_only_one_side_from_schema(builder, qtbot, caplog):
    """the schema defines only the minimum: ui:max is used, ui:min ignored."""
    widget = SpinSchemaWidget({"minimum": 1}, {"ui:min": 0, "ui:max": 20}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (1, 20)
    assert "ui:min 0" in caplog.text
    assert "ui:max" not in caplog.text


def test_ui_min_max_int_rounded_inwards(builder, qtbot):
    widget = SpinSchemaWidget({}, {"ui:min": 0.5, "ui:max": 9.5}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (1, 9)


def test_slider_bounds_from_ui_schema(builder, qtbot):
    widget = IntegerRangeSchemaWidget({}, {"ui:min": 0, "ui:max": 100, "ui:step": 5}, builder)
    qtbot.addWidget(widget)
    assert (widget.minimum(), widget.maximum()) == (0, 100)
    assert widget.singleStep() == 5


@pytest.mark.parametrize('cls, step', [(SpinSchemaWidget, 10), (SpinDoubleSchemaWidget, 0.25)])
def test_ui_step(cls, step, builder, qtbot, caplog):
    widget = cls({}, {"ui:step": step}, builder)
    qtbot.addWidget(widget)
    assert widget.singleStep() == step
    assert not caplog.records


@pytest.mark.parametrize('cls, multiple_of, ui_step', [
    (SpinSchemaWidget, 5, 10), (SpinDoubleSchemaWidget, 0.5, 1.5)])
def test_ui_step_multiple_of_multipleof(cls, multiple_of, ui_step, builder, qtbot, caplog):
    """ui:step overrides multipleOf if it is a multiple of it (valid values only)."""
    widget = cls({"multipleOf": multiple_of}, {"ui:step": ui_step}, builder)
    qtbot.addWidget(widget)
    assert widget.singleStep() == ui_step
    assert not caplog.records


@pytest.mark.parametrize('cls, multiple_of, ui_step', [
    (SpinSchemaWidget, 5, 3), (SpinDoubleSchemaWidget, 0.5, 0.3)])
def test_ui_step_conflict_schema_wins(cls, multiple_of, ui_step, builder, qtbot, caplog):
    widget = cls({"multipleOf": multiple_of}, {"ui:step": ui_step}, builder)
    qtbot.addWidget(widget)
    assert widget.singleStep() == multiple_of
    assert "not a multiple" in caplog.text


@pytest.mark.parametrize('ui_step', [0, -1, 2.5])
def test_ui_step_invalid_int(ui_step, builder, qtbot, caplog):
    widget = SpinSchemaWidget({}, {"ui:step": ui_step}, builder)
    qtbot.addWidget(widget)
    assert widget.singleStep() == 1
    assert "ui:step" in caplog.text


def test_int_multiple_of_fraction_keeps_default_step(builder, qtbot):
    """every integer fulfills multipleOf 0.5 - the step stays 1 (was a TypeError)."""
    widget = SpinSchemaWidget({"multipleOf": 0.5}, {}, builder)
    qtbot.addWidget(widget)
    assert widget.singleStep() == 1


def test_ui_decimals(builder, qtbot, caplog):
    widget = SpinDoubleSchemaWidget({}, {"ui:decimals": 4}, builder)
    qtbot.addWidget(widget)
    assert widget.decimals() == 4
    widget.state = 3.14159
    assert widget.state == pytest.approx(3.1416)
    assert not caplog.records


def test_ui_decimals_raised_for_schema(builder, qtbot, caplog):
    """too few decimals for multipleOf: the schema wins (warning)."""
    widget = SpinDoubleSchemaWidget({"multipleOf": 0.001}, {"ui:decimals": 1}, builder)
    qtbot.addWidget(widget)
    assert widget.decimals() == 3
    assert widget.singleStep() == pytest.approx(0.001)
    assert "raised to 3" in caplog.text


@pytest.mark.parametrize('schema, ui_schema, expected', [
    ({}, {}, 2),                              # Qt-default
    ({"multipleOf": 0.001}, {}, 3),           # needed by the schema
    ({"minimum": 0.125}, {}, 3),
    ({}, {"ui:step": 0.005}, 3),              # needed by ui:step
    ({"multipleOf": 0.5}, {}, 2),
])
def test_default_decimals(schema, ui_schema, expected, builder, qtbot):
    widget = SpinDoubleSchemaWidget(schema, ui_schema, builder)
    qtbot.addWidget(widget)
    assert widget.decimals() == expected


def test_minimum_not_rounded_away(builder, qtbot):
    """minimum 0.125 must not be rounded to 0.12/0.13 by the 2 default decimals."""
    widget = SpinDoubleSchemaWidget({"minimum": 0.125}, {}, builder)
    qtbot.addWidget(widget)
    assert widget.minimum() == 0.125


def test_ui_decimals_on_integer_warns(builder, qtbot, caplog):
    widget = SpinSchemaWidget({}, {"ui:decimals": 3}, builder)
    qtbot.addWidget(widget)
    assert "ui:decimals is not supported" in caplog.text


def test_ui_options_via_schema_widget(qtbot):
    """ui-options reach nested numeric fields through the ui-schema of SchemaWidget."""
    from pyqtschema import SchemaWidget

    schema = {"type": "object", "properties": {
        "count": {"type": "integer"},
        "ratio": {"type": "number", "minimum": 0, "maximum": 1}}}
    ui_schema = {"count": {"ui:min": 0, "ui:step": 10},
                 "ratio": {"ui:decimals": 3, "ui:step": 0.05}}
    widget = SchemaWidget(schema, ui_schema=ui_schema)
    qtbot.addWidget(widget)
    count, ratio = widget.widget.widgets["count"], widget.widget.widgets["ratio"]
    assert (count.minimum(), count.singleStep()) == (0, 10)
    assert (ratio.decimals(), ratio.singleStep()) == (3, 0.05)
