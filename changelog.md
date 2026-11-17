# Changelog

### Unreleased

* NEW: `SchemaWidget(schema, data=None, ...)` - high-level form for a JSON-schema, optionally filled with (partial)
  data; `state`, `on_changed`, `errors()`/`is_valid()`/`show_errors()`, `set_read_only()`, `set_translator()`
* NEW: `WidgetRegistry` - custom widgets per schema node, selected by `ui:widget`, field path, the schema-keyword
  `x-widget` or the `$ref`-definition name; registries can be layered (`child()`)
* NEW: `context` - application data handed from `SchemaWidget(..., context=...)`/`WidgetBuilder(..., context=...)` to
  every widget (`widget.context`), e.g. a data source for the choices of a custom widget; opaque to pyqtschema,
  `SchemaWidget.set_context()` rebuilds keeping the values
* NEW: `CustomObjectWidget` - base class for custom object-widgets (`setup_ui` + `build_field`, state pass-through of
  not-shown properties, error routing)
* NEW: `pyqtschema.pydantic_support` (extra `pyqtschema[pydantic]`, pydantic v2) - `ModelWidgetRegistry.register_model`,
  `model_schema`, `build_widget(model_or_instance, data)`, `to_model`
* NEW: `normalize_schema` (nullable `type`-lists, `null`-branches in `anyOf`/`oneOf`) and `translate_schema`
* NEW: `NullableSchemaWidget` - nullable fields (`int | None`, `Optional[Model]`, ...) get a checkbox for `None` in
  front of their widget; `normalize_schema` marks them with `x-nullable` instead of dropping the `null`-branch, so
  `None` is kept (was silently replaced by the widget default, e.g. `0`) and still validates.  A single typed branch
  is merged into a `type`-list (`{"type": ["integer", "null"], "minimum": 0}`) for specific validation-errors.
  `examples/nullable.py` shows all variants
* NEW: `NullableCheckboxSchemaWidget` - `Optional[bool]` is one tristate checkbox (partially checked: `None`) instead
  of a checkbox for `None` in front of a checkbox; while `None`, " (None)" is appended to the title
  (`"ui:show_none": false` hides it)
* NEW: `JsonSchemaWidget` - values of any type as JSON text: default for nodes without type (pydantic `Any`, `{}`;
  crashed the builder with `UnboundLocalError`) and objects without `properties` (`Dict[str, Any]`), selectable for
  every type with `"ui:widget": "json"`. A multi-line field (monospace, lists/objects indented) whose height fits
  the content and can be dragged with the grip in the bottom-right corner. Strict: invalid JSON is marked and the state
  keeps the last valid value.
  `Optional[Any]` gets no checkbox for `None` (null is a JSON value). `examples/any_value.py` shows all variants
* NEW: `"format": "color"` / `"ui:widget": "color"` selects the colour picker (only `"colour"` worked before, which
  stays as alias). `examples/color.py` shows all variants
* FIX: fields with a validation error get a red border (style sheet) - the palette colour used before was invisible
  in styles like `windows11` and set a white background on valid fields (broke dark themes); `VALID_COLOUR` is
  removed, `INVALID_COLOUR` is the border colour, `is_marked_invalid()` tells whether a field is marked
* FIX: spin boxes show their start value (an empty text was shown for `0` until the first change)
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
* FIX: number/integer spin boxes without `minimum` accept negative values (were silently clamped to `0`); the default
  range is the full 32-bit range for integers and unbounded for numbers, integer schema-bounds beyond 32 bit are clamped
  (logged) instead of raising an `OverflowError`
* FIX: `exclusiveMinimum`/`exclusiveMaximum` (pydantic `gt`/`lt`) are exclusive: integer spin boxes/sliders use the next
  integer (`gt=2` -> minimum `3`), number spin boxes move the bound by `multipleOf` or the smallest displayable step;
  the draft-4 boolean form is supported, if both `minimum` and `exclusiveMinimum` are given the stricter one wins
* NEW: ui-schema options of the numeric widgets: `ui:min`/`ui:max` (bounds if the schema defines none), `ui:step` (step
  of the arrows, must be a multiple of `multipleOf`), `ui:decimals` (decimals of a `number`); on a conflict the schema
  wins and a warning is logged
* `number` spin boxes show as many decimals as `multipleOf` and the bounds need (default still 2); an integer with a
  fractional `multipleOf` keeps the step `1` (was a `TypeError`)
* NEW: `examples/numeric.py` - all numeric scenarios side by side; every example is run as smoke-test
  (`tests/test_examples.py`)

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
