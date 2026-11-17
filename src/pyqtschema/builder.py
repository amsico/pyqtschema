import logging
from abc import abstractmethod
from copy import deepcopy
from typing import Any, Dict, Optional, Union

from . import widgets
from .registry import WidgetRegistry
from .schema import Schema, is_nullable, nullable_inner

logger = logging.getLogger(__name__)


def get_schema_type(schema: dict) -> str:
    return schema['type']


def has_schema_type(schema: Dict) -> bool:
    return 'type' in schema


def is_enum(schema: dict):
    return 'enum' in schema


def is_any_of(schema: dict):
    return 'anyOf' in schema


def is_one_of_const(schema: dict):
    """`oneOf` with plain `const`-alternatives (a labelled enum).

    The JSON-Schema-standard way to attach labels to enum-options
    (json-schema-spec#57): ``{"oneOf": [{"const": a, "title": "A"}, ...]}``.
    Rendered as a ComboBox by :class:`EnumSchemaWidget`.
    """
    alts = schema.get('oneOf')
    return isinstance(alts, list) and bool(alts) and all(
        isinstance(alt, dict) and 'const' in alt for alt in alts)


def is_all_of(schema: dict):
    return 'allOf' in schema


class IBuilder:
    """ Defines a builder-interface """

    @abstractmethod
    def create_widget(self, schema: dict, ui_schema: dict, state=None) -> 'widgets.SchemaWidgetMixin':
        raise NotImplementedError()


class WidgetBuilder(IBuilder):
    default_widget_map = {
        "boolean": {"checkbox": widgets.CheckboxSchemaWidget, "enum": widgets.EnumSchemaWidget},
        "object": {"object": widgets.ObjectSchemaWidget, "enum": widgets.EnumSchemaWidget},
        "number": {"spin": widgets.SpinDoubleSchemaWidget, "text": widgets.TextSchemaWidget,
                   "enum": widgets.EnumSchemaWidget},
        "string": {"textarea": widgets.TextAreaSchemaWidget, "text": widgets.TextSchemaWidget,
                   "password": widgets.PasswordWidget,
                   "path": widgets.FilepathSchemaWidget, "filepath": widgets.FilepathSchemaWidget,
                   "dirpath": widgets.DirectoryPathSchemaWidget,
                   "directory-path": widgets.DirectoryPathSchemaWidget,
                   "color": widgets.ColorSchemaWidget,
                   "colour": widgets.ColorSchemaWidget,  # alias of "color", kept for existing schemas
                   "enum": widgets.EnumSchemaWidget},
        "integer": {"spin": widgets.SpinSchemaWidget, "text": widgets.TextSchemaWidget,
                    "range": widgets.IntegerRangeSchemaWidget,
                    "enum": widgets.EnumSchemaWidget},
        "array": {"array": widgets.ArraySchemaWidget, "enum": widgets.EnumSchemaWidget},
        "enum": {"enum": widgets.EnumSchemaWidget},
        "anyOf": {"anyOf": widgets.AnyOfSchemaWidget, },
        "oneOf": {"enum": widgets.EnumSchemaWidget},
        "null": {"null": widgets.NullSchemaWidget},
        # a node without type (pydantic `Any`: `{}`) - any JSON value
        "any": {"json": widgets.JsonSchemaWidget},
    }
    # every type can be edited as JSON with `"ui:widget": "json"`
    for _variants in default_widget_map.values():
        _variants.setdefault("json", widgets.JsonSchemaWidget)
    del _variants

    default_widget_variants = {
        "boolean": "checkbox",
        "object": "object",
        "array": "array",
        "number": "spin",
        "integer": "spin",
        "string": "text",
        "enum": "enum",
        "anyOf": "anyOf",
        "oneOf": "enum",
        "directory-path": "dirpath",
        "null": "null",
        "any": "json",
    }

    widget_variant_modifiers = {
        "string": lambda schema: schema.get("format", "text"),
        # an object without properties (`Dict[str, Any]`) has nothing to lay out
        "object": lambda schema: "object" if schema.get("properties") else "json",
    }

    def __init__(
            self,
            schema: Union[Dict, Schema],
            validator_cls=None,
            registry: Optional[WidgetRegistry] = None,
            context: Any = None
    ):
        self.widget_map = deepcopy(self.default_widget_map)
        #: custom widgets, selected per schema-node (see :mod:`pyqtschema.registry`)
        self.registry: Optional[WidgetRegistry] = registry
        #: application data for custom widgets (e.g. a data source for choices); opaque to pyqtschema,
        #: available to every widget as ``self.context``
        self.context: Any = context

        self.schema: Schema = schema if isinstance(schema, Schema) else Schema(schema, validator_cls=validator_cls)
        self.schema.check_schema()

    def create_form(
            self,
            ui_schema: Optional[Dict] = None,
            state: Optional[Dict] = None,
            parent=None,
            validate: bool = True
    ) -> widgets.FormWidget:
        """Build the root widget wrapped in a :class:`FormWidget`.

        Field-path registrations of the ``registry`` are merged into
        ``ui_schema`` here.  With ``validate`` the state is validated on every
        change; :meth:`FormWidget.validate` works in either case.
        """
        if self.registry is not None:
            ui_schema = self.registry.apply_paths(ui_schema)
        elif ui_schema is None:
            ui_schema = {}

        schema_widget = self.create_widget(self.schema.schema, ui_schema, state)
        return widgets.FormWidget(schema_widget, parent=parent,
                                  validator=self.schema.validator(),
                                  live_validation=validate)

    def get_widget_state(self, schema, state=None):
        if state is None:
            return self.schema.compute_defaults(schema)
        return state

    def create_widget(self, schema: dict, ui_schema: dict, state=None, parent=None) -> widgets.SchemaWidgetMixin:
        ui_schema = ui_schema or {}
        # remember the reference *before* resolving it: the definition name
        # selects registered custom widgets (see `WidgetRegistry.resolve`)
        ref = schema.get('$ref') if isinstance(schema, dict) else None
        schema = self.schema.resolve_schema(schema)

        if is_nullable(schema):
            if nullable_inner(schema).get('type') == 'boolean' and 'ui:widget' not in ui_schema:
                # one tristate checkbox instead of a checkbox for None in front of a checkbox
                widget = widgets.NullableCheckboxSchemaWidget(schema, ui_schema, self, parent=parent)
            else:
                # checkbox for None around the widget of the editable part - the
                # inner widget is created by this builder (registry included)
                widget = widgets.NullableSchemaWidget(schema, ui_schema, self, parent=parent)
            return self._init_widget(widget, schema, state)

        if self.registry is not None:
            factory = self.registry.resolve(schema, ui_schema, ref)
            if factory is not None:
                return self._init_widget(factory(schema, ui_schema, self, parent=parent), schema, state)

        if is_one_of_const(schema):
            # `oneOf` with plain `const`-alternatives: a labelled enum
            # (standard-compliant way to label enum-options).  Checked before
            # the `type` key on purpose: pydantic emits both ``type`` and oneOf
            # for an enum-typed field - the enum-widget must win.
            schema_type = 'oneOf'
        elif has_schema_type(schema):
            schema_type = get_schema_type(schema)
        elif is_enum(schema):
            # schema created with pydantic do not have a type key for enum-values, always.
            # Therefore, the schema type "enum" is used in this case.
            schema_type = 'enum'
        elif is_any_of(schema):
            schema_type = 'anyOf'
        elif is_all_of(schema):
            # workaround for interesting allOf-pydantic behaviour
            if len(schema.get('allOf', [])) == 1:
                return self.create_widget(schema['allOf'][0], ui_schema, state=state, parent=parent)
            else:
                raise NotImplementedError('allOf is not supported')
        else:
            # no type and no combinator (pydantic `Any`, `{}`): any JSON value
            schema_type = 'any'

        try:
            default_variant = self.widget_variant_modifiers[schema_type](schema)
        except KeyError:
            default_variant = self.default_widget_variants[schema_type]

        if "enum" in schema:
            default_variant = "enum"

        widget_variant = ui_schema.get('ui:widget', default_variant)
        # Unknown `format` values (e.g. pydantic 'date-time'/'date'/'uri' on
        # string fields) or unsupported ui:widget variants would raise a
        # KeyError below.  Fall back to the type-default variant instead.
        variants = self.widget_map[schema_type]
        if widget_variant not in variants:
            candidate = self.default_widget_variants.get(schema_type)
            fallback_variant = candidate if candidate in variants else next(iter(variants))

            if 'ui:widget' in ui_schema:
                logger.warning(
                    "Unknown ui:widget %r for type %r is not supported; falling back to %r. "
                    "The data may not be rendered as intended.",
                    widget_variant, schema_type, fallback_variant,
                )
            else:
                logger.warning(
                    "Unknown format %r for type %r is not supported; falling back to %r. "
                    "The data may not be rendered as intended.",
                    widget_variant, schema_type, fallback_variant,
                )
            widget_variant = fallback_variant
        widget_cls = variants[widget_variant]

        widget = widget_cls(schema, ui_schema, self, parent=parent)
        return self._init_widget(widget, schema, state)

    def _init_widget(self, widget: widgets.SchemaWidgetMixin, schema: dict, state=None) -> widgets.SchemaWidgetMixin:
        default_state = self.get_widget_state(schema, state)
        if default_state is not None:
            widget.state = default_state
        return widget
