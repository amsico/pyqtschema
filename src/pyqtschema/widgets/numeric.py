"""Widgets for ``integer`` and ``number`` schema nodes.

* :class:`SpinSchemaWidget` - ``integer`` (default), a ``QSpinBox``
* :class:`SpinDoubleSchemaWidget` - ``number`` (default), a ``QDoubleSpinBox``
* :class:`IntegerRangeSchemaWidget` - ``integer`` with ``"ui:widget": "range"``, a ``QSlider``

Configuration
-------------
The **schema** holds the rules for the data - they are validated.  The
pydantic ``Field``-arguments are given in brackets:

``minimum`` (``ge``), ``maximum`` (``le``)
    inclusive bounds.
``exclusiveMinimum`` (``gt``), ``exclusiveMaximum`` (``lt``)
    exclusive bounds: an integer uses the next integer (``gt=2`` -> ``3``), a
    number moves the bound inwards by ``multipleOf`` or else by the smallest
    displayable step (``gt=0`` -> ``0.01`` with 2 decimals).  The draft-4 form
    (a boolean modifying ``minimum``/``maximum``) is supported; if both
    ``minimum`` and ``exclusiveMinimum`` are given, the stricter one wins.
``multipleOf`` (``multiple_of``)
    step size of the arrows - **and** a validation rule.

The **ui-schema** only changes the presentation, never the data rules:

``ui:min``, ``ui:max``
    bounds used if the schema defines none (e.g. a slider for an unbounded
    field).  If the schema defines the bound, the schema wins and a
    deviating ``ui:min``/``ui:max`` is logged as warning.
``ui:step``
    step size of the arrows (instead of ``multipleOf`` / ``1``).  It must be a
    multiple of ``multipleOf``, otherwise ``multipleOf`` is used (warning).
``ui:decimals``
    displayed decimals of a ``number`` (default: 2, or more if the schema
    needs them).  Too few decimals for the schema-values are raised (warning).

Without bounds the full range of the widget is used: ``-2**31 .. 2**31-1`` for
an integer (``QSpinBox`` stores a 32-bit int on every platform Qt supports;
bounds outside are clamped with a warning) and ``-inf .. inf`` for a number.

Example::

    class Model(BaseModel):
        count: int = Field(3, gt=0, le=100)
        ratio: float = Field(0.5, ge=0, le=1)

    ui_schema = {"count": {"ui:step": 10}, "ratio": {"ui:decimals": 3, "ui:step": 0.05}}
    SchemaWidget(Model.model_json_schema(), ui_schema=ui_schema)

See ``examples/numeric.py`` for all scenarios.
"""
import logging
import math
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDoubleSpinBox, QSpinBox, QSlider

from pyqtschema.widgets.base import SchemaWidgetMixin, state_property

if TYPE_CHECKING:  # pragma: no cover
    from pyqtschema.builder import WidgetBuilder

logger = logging.getLogger(__name__)

Number = Union[int, float]

#: QSpinBox stores a C++ int - 32 bit on every platform Qt supports.  Used
#: without a `minimum`/`maximum` in the schema; bounds outside are clamped.
INT_MINIMUM = -2 ** 31
INT_MAXIMUM = 2 ** 31 - 1
#: QDoubleSpinBox stores a double: no bound needed without `minimum`/`maximum`
FLOAT_MINIMUM = float('-inf')
FLOAT_MAXIMUM = float('inf')

#: decimals of a ``number`` spin box without ``ui:decimals`` (Qt-default)
DEFAULT_DECIMALS = 2
#: upper limit of the decimals derived from the schema
MAX_DECIMALS = 10

#: ui-schema keywords of the numeric widgets
UI_MIN = 'ui:min'
UI_MAX = 'ui:max'
UI_STEP = 'ui:step'
UI_DECIMALS = 'ui:decimals'

#: a bound of the schema: (value, exclusive)
Bound = Tuple[float, bool]


def _label(schema: dict) -> str:
    return repr(schema.get('title', schema))


def _schema_bound(schema: dict, key: str, exclusive_key: str, lower: bool) -> Optional[Bound]:
    """The effective bound for `minimum`/`exclusiveMinimum` (or the maxima).

    https://json-schema.org/understanding-json-schema/reference/numeric#range

    * draft 6+: ``exclusiveMinimum`` is a number of its own; if both keywords
      are given, the stricter one wins.
    * draft 4: ``exclusiveMinimum`` is a boolean modifying ``minimum``.
    """
    value = schema.get(key)
    exclusive = schema.get(exclusive_key)
    if isinstance(exclusive, bool):  # draft 4 (check first: bool is an int)
        return None if value is None else (value, exclusive)

    candidates: List[Bound] = []
    if value is not None:
        candidates.append((value, False))
    if exclusive is not None:
        candidates.append((exclusive, True))
    if not candidates:
        return None
    # stricter: the larger minimum / smaller maximum; on a tie the exclusive one
    if lower:
        return max(candidates, key=lambda b: (b[0], b[1]))
    return min(candidates, key=lambda b: (b[0], not b[1]))


def schema_bounds(schema: dict) -> Tuple[Optional[Bound], Optional[Bound]]:
    """(lower, upper) bound of a numeric schema, each ``(value, exclusive)`` or None."""
    return (_schema_bound(schema, 'minimum', 'exclusiveMinimum', lower=True),
            _schema_bound(schema, 'maximum', 'exclusiveMaximum', lower=False))


def int_range_from_schema(schema: dict) -> Tuple[Optional[int], Optional[int]]:
    """Inclusive integer range: ``exclusiveMinimum: 2`` -> 3, ``exclusiveMaximum: 10`` -> 9."""
    lower, upper = schema_bounds(schema)
    minimum = maximum = None
    if lower is not None:
        value, exclusive = lower
        minimum = math.floor(value) + 1 if exclusive else math.ceil(value)
    if upper is not None:
        value, exclusive = upper
        maximum = math.ceil(value) - 1 if exclusive else math.floor(value)
    return minimum, maximum


def float_range_from_schema(schema: dict, epsilon: float) -> Tuple[Optional[float], Optional[float]]:
    """Inclusive float range; an exclusive bound is moved inwards by ``epsilon``."""
    lower, upper = schema_bounds(schema)
    minimum = maximum = None
    if lower is not None:
        value, exclusive = lower
        minimum = value + epsilon if exclusive else value
    if upper is not None:
        value, exclusive = upper
        maximum = value - epsilon if exclusive else value
    return minimum, maximum


def _ui_bound(schema_value: Optional[Number], ui_schema: dict, ui_key: str,
              schema: dict, integer: bool) -> Optional[Number]:
    """`ui:min`/`ui:max` - only used if the schema defines no bound."""
    ui_value = ui_schema.get(ui_key)
    if ui_value is None:
        return schema_value
    if schema_value is not None:
        if ui_value != schema_value:
            logger.warning("%s %r of %s is ignored: the schema defines the bound %r.",
                           ui_key, ui_value, _label(schema), schema_value)
        return schema_value
    if integer:
        return math.ceil(ui_value) if ui_key == UI_MIN else math.floor(ui_value)
    return ui_value


def _clamp_int_bound(name: str, value: int, schema: dict) -> int:
    clamped = min(max(value, INT_MINIMUM), INT_MAXIMUM)
    if clamped != value:
        logger.warning("%s %r of %s exceeds the 32-bit range of the spin box; clamped to %r.",
                       name, value, _label(schema), clamped)
    return clamped


def int_range(schema: dict, ui_schema: dict) -> Tuple[Optional[int], Optional[int]]:
    """Range of an integer widget: schema-bounds, else ``ui:min``/``ui:max`` (None if neither)."""
    minimum, maximum = int_range_from_schema(schema)
    minimum = _ui_bound(minimum, ui_schema, UI_MIN, schema, integer=True)
    maximum = _ui_bound(maximum, ui_schema, UI_MAX, schema, integer=True)
    if minimum is not None:
        minimum = _clamp_int_bound('minimum', minimum, schema)
    if maximum is not None:
        maximum = _clamp_int_bound('maximum', maximum, schema)
    return minimum, maximum


def float_range(schema: dict, ui_schema: dict, epsilon: float) -> Tuple[Optional[float], Optional[float]]:
    """Range of a number widget: schema-bounds, else ``ui:min``/``ui:max`` (None if neither)."""
    minimum, maximum = float_range_from_schema(schema, epsilon)
    return (_ui_bound(minimum, ui_schema, UI_MIN, schema, integer=False),
            _ui_bound(maximum, ui_schema, UI_MAX, schema, integer=False))


def _is_multiple(value: Number, base: Number) -> bool:
    quotient = value / base
    return math.isclose(quotient, round(quotient), abs_tol=1e-9)


def step_size(schema: dict, ui_schema: dict, integer: bool) -> Optional[Number]:
    """Step of the arrows: ``ui:step`` if it fits the schema, else ``multipleOf`` (None: Qt-default)."""
    multiple_of = schema.get('multipleOf')
    if integer and multiple_of is not None:
        # every integer fulfills e.g. `multipleOf: 0.5` - only an integral step is usable
        multiple_of = int(multiple_of) if float(multiple_of).is_integer() else None

    ui_step = ui_schema.get(UI_STEP)
    if ui_step is None:
        return multiple_of
    if ui_step <= 0 or (integer and not float(ui_step).is_integer()):
        logger.warning("%s %r of %s is ignored: a %s step is required.",
                       UI_STEP, ui_step, _label(schema),
                       "positive integral" if integer else "positive")
        return multiple_of
    if multiple_of is not None and not _is_multiple(ui_step, multiple_of):
        logger.warning("%s %r of %s is ignored: it is not a multiple of the schema's multipleOf %r.",
                       UI_STEP, ui_step, _label(schema), multiple_of)
        return multiple_of
    return int(ui_step) if integer else ui_step


def _decimal_places(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return 0
    exponent = Decimal(repr(value)).normalize().as_tuple().exponent
    return max(0, -exponent)


def decimals(schema: dict, ui_schema: dict) -> int:
    """Decimals of a number widget.

    The schema-values (``multipleOf`` and the bounds) must be displayable: if
    ``ui:decimals`` is too small, it is raised (warning).  Without
    ``ui:decimals`` the default (2) is raised as well, also for ``ui:step``.
    """
    keys = ('multipleOf', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum')
    needed = min(MAX_DECIMALS, max(_decimal_places(schema.get(key)) for key in keys))

    ui_decimals = ui_schema.get(UI_DECIMALS)
    if ui_decimals is None:
        return max(DEFAULT_DECIMALS, needed, min(MAX_DECIMALS, _decimal_places(ui_schema.get(UI_STEP))))
    if ui_decimals < needed:
        logger.warning("%s %r of %s is raised to %r: the schema-values need more decimals.",
                       UI_DECIMALS, ui_decimals, _label(schema), needed)
        return needed
    return ui_decimals


def _warn_unsupported(schema: dict, ui_schema: dict, *keys: str) -> None:
    for key in keys:
        if key in ui_schema:
            logger.warning("%s is not supported for %s and ignored.", key, _label(schema))


class SpinSchemaWidget(SchemaWidgetMixin, QSpinBox):
    """``integer`` as ``QSpinBox`` (default widget of an integer).

    Schema: ``minimum``/``exclusiveMinimum`` (``ge``/``gt``),
    ``maximum``/``exclusiveMaximum`` (``le``/``lt``), ``multipleOf``.
    ui-schema: ``ui:min``, ``ui:max``, ``ui:step``.
    Without bounds: ``-2**31 .. 2**31-1``.  See :mod:`pyqtschema.widgets.numeric`.
    """

    @state_property
    def state(self) -> int:
        return self.value()

    @state.setter
    def state(self, state: int):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)
        ui_schema = self.ui_schema or {}
        _warn_unsupported(self.schema, ui_schema, UI_DECIMALS)

        step = step_size(self.schema, ui_schema, integer=True)
        if step is not None:
            self.setSingleStep(step)

        # without a bound the Qt-defaults would apply (minimum 0, maximum 99),
        # silently clamping e.g. negative values - use the full range instead
        minimum, maximum = int_range(self.schema, ui_schema)
        self.setMaximum(INT_MAXIMUM if maximum is None else maximum)
        self.setMinimum(INT_MINIMUM if minimum is None else minimum)
        # Qt shows an empty text until the first `setValue` (e.g. for the start value 0)
        self.setValue(self.value())


class SpinDoubleSchemaWidget(SchemaWidgetMixin, QDoubleSpinBox):
    """``number`` as ``QDoubleSpinBox`` (default widget of a number).

    Schema: ``minimum``/``exclusiveMinimum`` (``ge``/``gt``),
    ``maximum``/``exclusiveMaximum`` (``le``/``lt``), ``multipleOf``.
    ui-schema: ``ui:min``, ``ui:max``, ``ui:step``, ``ui:decimals``.
    Without bounds: ``-inf .. inf``.  See :mod:`pyqtschema.widgets.numeric`.
    """

    @state_property
    def state(self) -> float:
        return self.value()

    @state.setter
    def state(self, state: float):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)
        ui_schema = self.ui_schema or {}

        # first: Qt rounds the range (and the value) to the decimals
        self.setDecimals(decimals(self.schema, ui_schema))

        step = step_size(self.schema, ui_schema, integer=False)
        if step is not None:
            self.setSingleStep(step)

        # an exclusive bound is moved by one step of `multipleOf` (a data rule,
        # not `ui:step`) or else by the smallest value the spin box can display
        epsilon = self.schema.get('multipleOf') or 10 ** -self.decimals()
        minimum, maximum = float_range(self.schema, ui_schema, epsilon)
        # without a bound the Qt-defaults would apply (minimum 0, maximum 99.99),
        # silently clamping e.g. negative values - leave the range open instead
        self.setMaximum(FLOAT_MAXIMUM if maximum is None else maximum)
        self.setMinimum(FLOAT_MINIMUM if minimum is None else minimum)
        # Qt shows an empty text until the first `setValue` (e.g. for the start value 0)
        self.setValue(self.value())


class IntegerRangeSchemaWidget(SchemaWidgetMixin, QSlider):
    """``integer`` as horizontal ``QSlider`` (``"ui:widget": "range"``).

    Needs a lower and an upper bound - from the schema or ``ui:min``/``ui:max``.
    ``multipleOf`` or ``ui:step`` set the step and the tick interval.
    See :mod:`pyqtschema.widgets.numeric`.
    """

    def __init__(self, schema: dict, ui_schema: dict, widget_builder: 'WidgetBuilder', *args, **kwargs):
        kwargs['orientation'] = Qt.Horizontal
        super().__init__(schema, ui_schema, widget_builder, *args, **kwargs)

    @state_property
    def state(self) -> int:
        return self.value()

    @state.setter
    def state(self, state: int):
        self.setValue(state)

    def configure(self):
        self.valueChanged.connect(self.on_changed.emit)
        ui_schema = self.ui_schema or {}
        _warn_unsupported(self.schema, ui_schema, UI_DECIMALS)

        step = step_size(self.schema, ui_schema, integer=True)
        if step:
            self.setTickInterval(step)
            self.setSingleStep(step)
            self.setTickPosition(QSlider.TickPosition.TicksBothSides)

        minimum, maximum = int_range(self.schema, ui_schema)
        if minimum is None or maximum is None:
            raise ValueError('Cannot create a slider without boundary conditions '
                             '(minimum/maximum in the schema or ui:min/ui:max)')
        self.setRange(minimum, maximum)
