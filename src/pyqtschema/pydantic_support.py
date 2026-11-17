"""pydantic (v2) helpers - optional, requires ``pip install pyqtschema[pydantic]``.

* :class:`ModelWidgetRegistry` - register custom widgets by *model class*
  (subclasses inherit the widget of their base class),
* :func:`model_schema` - the JSON-schema of a model with the ``x-widget``
  markers of the registered models,
* :func:`build_widget` - a :class:`~pyqtschema.SchemaWidget` from a model
  class or instance plus optional data,
* :func:`to_model` - validate the state of a form into a model instance.

The core (:class:`~pyqtschema.SchemaWidget`, :class:`~pyqtschema.WidgetRegistry`)
works on plain JSON-schema dicts; this module only translates model classes
into schema markers.
"""
import typing
from typing import Any, Callable, Dict, Iterator, Optional, Set, Type, Union

try:
    from pydantic import BaseModel
except ImportError as err:  # pragma: no cover - depends on the environment
    raise ImportError("pyqtschema.pydantic_support requires pydantic>=2 "
                      "(pip install pyqtschema[pydantic])") from err

from .registry import SCHEMA_WIDGET_KEY, WidgetFactory, WidgetRegistry
from .schema_widget import SchemaWidget

SchemaFactory = Callable[[Type[BaseModel]], Dict]

__all__ = ["ModelWidgetRegistry", "model_schema", "build_widget", "to_model", "iter_models"]


def _qualname(model: type) -> str:
    return f"{model.__module__}.{model.__qualname__}"


class ModelWidgetRegistry(WidgetRegistry):
    """:class:`WidgetRegistry` that additionally maps model classes to widgets."""

    def __init__(self, parent: Optional[WidgetRegistry] = None) -> None:
        super().__init__(parent)
        self._models: Dict[type, str] = {}

    def register_model(self, model: Type[BaseModel], factory: Optional[WidgetFactory] = None, *,
                       name: Optional[str] = None, replace: bool = False) -> str:
        """Render every occurrence of ``model`` (and its subclasses) with ``factory``.

        Args:
            model: the pydantic model class.
            factory: widget class/factory; None maps ``model`` to an already
                registered widget ``name``.
            name: widget name (default: the qualified class name).
            replace: allow re-registering ``name`` in this layer.
        """
        name = name or _qualname(model)
        if factory is not None:
            self.register(name, factory, replace=replace)
        elif not self.has(name):
            raise ValueError(f"widget {name!r} is not registered")
        self._models[model] = name
        return name

    def model_widget(self, model: type) -> Optional[str]:
        """The widget name for ``model`` (by MRO, searching parent layers)."""
        for cls in getattr(model, "__mro__", (model,)):
            name = self._own_model_widget(cls)
            if name is not None:
                return name
        return None

    def _own_model_widget(self, cls: type) -> Optional[str]:
        if cls in self._models:
            return self._models[cls]
        parent = self.parent
        if isinstance(parent, ModelWidgetRegistry):
            return parent._own_model_widget(cls)
        return None


def iter_models(model: Type[BaseModel]) -> Iterator[Type[BaseModel]]:
    """``model`` and all models reachable through its field annotations."""
    seen: Set[type] = set()
    stack = [model]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        yield current
        for field in current.model_fields.values():
            stack.extend(m for m in _annotation_models(field.annotation) if m not in seen)


def _annotation_models(annotation: Any) -> Iterator[Type[BaseModel]]:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        yield annotation
        return
    for arg in typing.get_args(annotation):
        yield from _annotation_models(arg)


def model_schema(model: Type[BaseModel], registry: Optional[WidgetRegistry] = None,
                 schema_factory: Optional[SchemaFactory] = None) -> Dict:
    """The JSON-schema of ``model`` including the ``x-widget`` markers.

    For every model reachable from ``model`` that has a registered widget
    (:meth:`ModelWidgetRegistry.register_model`), the ``x-widget`` keyword is
    set on its definition (``$defs``-entry named like the class) or - for
    ``model`` itself - on the root schema.  Existing markers are kept.

    Args:
        model: the model class.
        registry: widget registry (markers only for a :class:`ModelWidgetRegistry`).
        schema_factory: creates the schema (default: ``model.model_json_schema()``).
    """
    schema = (schema_factory or (lambda m: m.model_json_schema()))(model)
    if not isinstance(registry, ModelWidgetRegistry):
        return schema
    defs = schema.get("$defs") or schema.get("definitions") or {}
    for cls in iter_models(model):
        name = registry.model_widget(cls)
        if name is None:
            continue
        node = schema if cls is model else defs.get(cls.__name__)
        if isinstance(node, dict):
            node.setdefault(SCHEMA_WIDGET_KEY, name)
    return schema


def _deep_merge(base: Any, update: Any) -> Any:
    if isinstance(base, dict) and isinstance(update, dict):
        out = dict(base)
        for key, value in update.items():
            out[key] = _deep_merge(base.get(key), value) if key in base else value
        return out
    return update


def build_widget(model: Union[Type[BaseModel], BaseModel], data: Optional[Dict] = None, *,
                 registry: Optional[WidgetRegistry] = None,
                 schema_factory: Optional[SchemaFactory] = None,
                 **kwargs) -> SchemaWidget:
    """A :class:`~pyqtschema.SchemaWidget` for a model class or instance.

    Args:
        model: model class (defaults) or instance (its values,
            ``model_dump(mode="json")``).
        data: values (deep-)merged over the instance values / defaults.
        registry: custom widgets (model classes via :class:`ModelWidgetRegistry`).
        schema_factory: creates the schema (default: ``model_json_schema()``).
        **kwargs: passed to :class:`~pyqtschema.SchemaWidget`.
    """
    cls = type(model) if isinstance(model, BaseModel) else model
    values = model.model_dump(mode="json") if isinstance(model, BaseModel) else None
    if data is not None:
        values = _deep_merge(values, data) if values is not None else data
    schema = model_schema(cls, registry=registry, schema_factory=schema_factory)
    widget = SchemaWidget(schema, values, registry=registry, **kwargs)
    widget.model = cls
    return widget


def to_model(widget: SchemaWidget, model: Optional[Type[BaseModel]] = None) -> BaseModel:
    """Validate the state of ``widget`` into an instance of ``model``.

    ``model`` defaults to the model the widget was built from by
    :func:`build_widget`; raises :class:`pydantic.ValidationError`.
    """
    cls = model or getattr(widget, "model", None)
    if cls is None:
        raise ValueError("to_model: no model given and the widget was not built by build_widget")
    return cls.model_validate(widget.state)
