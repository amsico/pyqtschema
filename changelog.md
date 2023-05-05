# Changelog

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
