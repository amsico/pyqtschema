"""High-level form widget: a JSON-schema plus optional data."""
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QVBoxLayout, QWidget

from .builder import WidgetBuilder
from .schema import Translator, normalize_schema, translate_schema
from .registry import WidgetRegistry
from .widgets.base import SchemaWidgetMixin
from .widgets.readonly import apply_read_only
from .widgets.root import FormWidget


class SchemaWidget(QWidget):
    """A form for a JSON-schema, optionally filled with data.

    ``SchemaWidget(schema, data)`` renders ``schema`` - generic widgets by
    default, custom widgets where the ``registry`` selects one - and fills it
    with ``data``.  Properties missing in ``data`` keep their schema-defaults,
    unknown keys are ignored.

    Args:
        schema: the JSON-schema (e.g. ``MyModel.model_json_schema()``).
        data: initial values (optional, may be partial).
        ui_schema: ui-schema (``ui:hidden``, ``ui:widget``, ...).
        registry: custom widgets (see :class:`~pyqtschema.registry.WidgetRegistry`).
        translator: applied to every ``title``/``description`` at build-time;
            :meth:`set_translator` rebuilds the form keeping the values.
        normalize: normalize nullable constructs (see
            :func:`~pyqtschema.schema.normalize_schema`).
        validate: validate the state on every change and show the errors.
        validator_cls: jsonschema validator class (default: by ``$schema``).
        parent: Qt parent.
    """

    #: emitted with the new state on every change
    on_changed = Signal(object)

    def __init__(
            self,
            schema: Dict,
            data: Optional[Any] = None,
            *,
            ui_schema: Optional[Dict] = None,
            registry: Optional[WidgetRegistry] = None,
            translator: Optional[Translator] = None,
            normalize: bool = True,
            validate: bool = True,
            validator_cls: Optional[Callable] = None,
            parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self._raw_schema = deepcopy(schema)
        self._raw_ui_schema = deepcopy(ui_schema or {})
        self._registry = registry
        self._translator = translator
        self._normalize = normalize
        self._validate = validate
        self._validator_cls = validator_cls
        self._read_only = False

        self._builder: Optional[WidgetBuilder] = None
        self._form: Optional[FormWidget] = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._build(data)

    # -- building ---------------------------------------------------------
    def _prepare_schema(self) -> Dict:
        schema = normalize_schema(self._raw_schema) if self._normalize else deepcopy(self._raw_schema)
        return translate_schema(schema, self._translator)

    def _build(self, data: Optional[Any] = None) -> None:
        if self._form is not None:
            self._layout.removeWidget(self._form)
            self._form.deleteLater()
            self._form = None

        schema = self._prepare_schema()
        builder = WidgetBuilder(schema, validator_cls=self._validator_cls, registry=self._registry)
        form = builder.create_form(deepcopy(self._raw_ui_schema), parent=self, validate=self._validate)
        if data is not None:
            form.widget.state = data
        form.widget.on_changed.connect(self.on_changed.emit)

        self._builder = builder
        self._form = form
        self._layout.addWidget(form)
        if self._read_only:
            apply_read_only(form.widget, True)

    def rebuild(self, preserve_state: bool = True) -> None:
        """Rebuild the form (e.g. after changing the registry)."""
        self._build(self.state if preserve_state else None)

    def set_translator(self, translator: Optional[Translator]) -> None:
        """Switch the translator and rebuild the form keeping the values."""
        self._translator = translator
        self.rebuild(preserve_state=True)

    # -- accessors --------------------------------------------------------
    @property
    def schema(self) -> Dict:
        """The prepared (normalized/translated) schema the form is built from."""
        return self._builder.schema.schema

    @property
    def registry(self) -> Optional[WidgetRegistry]:
        return self._registry

    @property
    def builder(self) -> WidgetBuilder:
        return self._builder

    @property
    def form(self) -> FormWidget:
        """The inner :class:`FormWidget` (root widget + error display)."""
        return self._form

    @property
    def widget(self) -> SchemaWidgetMixin:
        """The root schema-widget."""
        return self._form.widget

    # -- state ------------------------------------------------------------
    @property
    def state(self) -> Any:
        return self._form.widget.state

    @state.setter
    def state(self, value: Any) -> None:
        self._form.widget.state = value

    def errors(self) -> List[Exception]:
        """Validation-errors of the current state (jsonschema errors), not displayed."""
        return list(self._form.validator.iter_errors(self.state))

    def is_valid(self) -> bool:
        return not self.errors()

    def show_errors(self) -> bool:
        """Validate the current state, show the errors and mark the fields; True if valid."""
        return not self._form.validate()

    # -- read-only --------------------------------------------------------
    def set_read_only(self, read_only: bool) -> None:
        """Enable/disable all editors (custom widgets may define ``set_read_only``)."""
        self._read_only = bool(read_only)
        apply_read_only(self._form.widget, self._read_only)

    def is_read_only(self) -> bool:
        return self._read_only
