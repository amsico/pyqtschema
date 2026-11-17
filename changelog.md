# Changelog

### Unreleased

* NEW: `SchemaWidget(schema, data=None, ...)` - high-level form for a JSON-schema, optionally filled with (partial)
  data; `state`, `on_changed`, `errors()`/`is_valid()`/`show_errors()`, `set_read_only()`, `set_translator()`
* NEW: `WidgetRegistry` - custom widgets per schema node, selected by `ui:widget`, field path, the schema-keyword
  `x-widget` or the `$ref`-definition name; registries can be layered (`child()`)
* NEW: `CustomObjectWidget` - base class for custom object-widgets (`setup_ui` + `build_field`, state pass-through of
  not-shown properties, error routing)
* NEW: `pyqtschema.pydantic_support` (extra `pyqtschema[pydantic]`, pydantic v2) - `ModelWidgetRegistry.register_model`,
  `model_schema`, `build_widget(model_or_instance, data)`, `to_model`
* NEW: `normalize_schema` (nullable `type`-lists, `null`-branches in `anyOf`/`oneOf`) and `translate_schema`
* NEW: `set_widgets_read_only` / `apply_read_only`
* `WidgetBuilder(schema, registry=...)` honors custom widgets, `create_form` also applies the field-path registrations
* `WidgetBuilder.create_form(..., validate=True)` - `validate=False` disables the validation on every change
* NEW: `FormWidget.validate(data=None)` - validate, show the errors and mark the affected fields; used by
  `create_form` and `SchemaWidget.show_errors()` (which now also marks the fields)
* NEW: `NullSchemaWidget` for `{"type": "null"}` - the raw `WidgetBuilder` no longer fails with `KeyError: 'null'`
  on not-normalized nullable fields (the `null`-branch of an `anyOf` is shown as a choice)
* `Schema.resolve_schema` merges the sibling keywords of a `$ref` (`title`, `description`, `default`) and follows
  nested references
* `ObjectSchemaWidget.state` ignores unknown properties (logged) instead of raising a `KeyError`

### Version 0.2.0 (2023-05-05)

* use [QtPy](https://pypi.org/project/QtPy/) instead of `PyQt5`

### Version 0.1.9 (2022-07-12)

* FIX: default calculation for simple AllOf-cases
* New example for ui_schema usage
* New example for simple AllOf case

### Version 0.1.8 (2022-07-04)

* state-setter in EnumWidget supports Enum-objects
* FIX: is_valid_data function in Schema returned wrong results
* FIX: AnyOf-Widget was not working properly with several types of the same type (issue #13)
* add first testing for EnumWidget
* renamed some examples

### Version 0.1.7 (2022-02-11)

* improve the readme-file
* add simple load/save functionality to the application
* add changelog to project-description
* add workaround for pydantic-allOf schema

### Version 0.1.6 (2022-02-10)

* improve anyOf support:
    * setting a state may modify the combo-box (if entry was changed)
    * improve default-support

### Version 0.1.5 (2022-02-09)

* improve path/directory-support

### Version 0.1.4 (2022-02-04)

* improve visibility of widgets (relevant widgets scale)
* add `parent` parameter to create_widget in builder
* pass parent to QWidgets to avoid flickering during the initialization

### Version 0.1.3 (2022-02-03)

* support `ui:hidden` in ui_schema (hide an unwanted widget; default is False)
* support `ui:disabled` in ui_schema (disable an unwanted widget; default is False)
* support parent parameter in create_form-function (Issue #6)

### Version 0.1.2 (2022-02-02)

* first official release on pypi: https://pypi.org/project/pyqtschema/
