from copy import deepcopy
from typing import Dict, Optional, Union

from . import widgets
from .builder_base import IBuilder
from .schema import Schema


def get_schema_type(schema: dict) -> str:
    return schema['type']


def has_schema_type(schema: Dict) -> bool:
    return 'type' in schema


def is_enum(schema: dict):
    return 'enum' in schema


def is_any_of(schema: dict):
    return 'anyOf' in schema


class WidgetBuilder(IBuilder):
    default_widget_map = {
        "boolean": {"checkbox": widgets.CheckboxSchemaWidget, "enum": widgets.EnumSchemaWidget},
        "object": {"object": widgets.ObjectSchemaWidget, "enum": widgets.EnumSchemaWidget},
        "number": {"spin": widgets.SpinDoubleSchemaWidget, "text": widgets.TextSchemaWidget,
                   "enum": widgets.EnumSchemaWidget},
        "string": {"textarea": widgets.TextAreaSchemaWidget, "text": widgets.TextSchemaWidget,
                   "password": widgets.PasswordWidget,
                   "filepath": widgets.FilepathSchemaWidget, "dirpath": widgets.DirectorypathSchemaWidget,
                   "colour": widgets.ColorSchemaWidget, "enum": widgets.EnumSchemaWidget},
        "integer": {"spin": widgets.SpinSchemaWidget, "text": widgets.TextSchemaWidget,
                    "range": widgets.IntegerRangeSchemaWidget,
                    "enum": widgets.EnumSchemaWidget},
        "array": {"array": widgets.ArraySchemaWidget, "enum": widgets.EnumSchemaWidget},
        "enum": {"enum": widgets.EnumSchemaWidget},
        "anyOf": {"anyOf": widgets.AnyOfSchemaWidget, },
    }

    default_widget_variants = {
        "boolean": "checkbox",
        "object": "object",
        "array": "array",
        "number": "spin",
        "integer": "spin",
        "string": "text",
        "enum": "enum",
        "anyOf": "anyOf",
    }

    widget_variant_modifiers = {
        "string": lambda schema: schema.get("format", "text")
    }

    def __init__(self, schema: Union[Dict, Schema], validator_cls=None):
        self.widget_map = deepcopy(self.default_widget_map)

        self.schema: Schema = schema if isinstance(schema, Schema) else Schema(schema, validator_cls=validator_cls)
        self.schema.check_schema()

    def create_form(self,
                    ui_schema: Optional[Dict] = None,
                    state: Optional[Dict] = None,
                    parent=None) \
            -> widgets.SchemaWidgetMixin:
        if ui_schema is None:
            ui_schema = {}

        schema_widget = self.create_widget(self.schema.schema, ui_schema, state)
        form = widgets.FormWidget(schema_widget, parent=parent)

        _validator = self.schema.validator()

        def validate(data):
            form.clear_errors()
            errors = [*_validator.iter_errors(data)]

            if errors:
                form.display_errors(errors)

            for err in errors:
                schema_widget.handle_error(err.path, err)

        schema_widget.on_changed.connect(validate)

        return form

    def get_widget_state(self, schema, state=None):
        if state is None:
            return self.schema.compute_defaults(schema)
        return state

    def create_widget(self, schema: dict, ui_schema: dict, state=None, parent=None) -> widgets.SchemaWidgetMixin:
        schema = self.schema.resolve_schema(schema)

        if has_schema_type(schema):
            schema_type = get_schema_type(schema)
        elif is_enum(schema):
            # schema created with pydantic do not have a type key for enum-values, always.
            # Therefore, the schema type "enum" is used in this case.
            schema_type = 'enum'
        elif is_any_of(schema):
            schema_type = 'anyOf'

        try:
            default_variant = self.widget_variant_modifiers[schema_type](schema)
        except KeyError:
            default_variant = self.default_widget_variants[schema_type]

        if "enum" in schema:
            default_variant = "enum"

        widget_variant = ui_schema.get('ui:widget', default_variant)
        widget_cls = self.widget_map[schema_type][widget_variant]

        widget = widget_cls(schema, ui_schema, self, parent=parent)

        default_state = self.get_widget_state(schema, state)
        if default_state is not None:
            widget.state = default_state
        return widget
