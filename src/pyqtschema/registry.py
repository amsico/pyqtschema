"""Registry of custom widgets (Qt-free).

A :class:`WidgetRegistry` maps *names* to widget factories and decides which
(sub-)schema is rendered by a custom widget instead of the generic one.  It
works on plain JSON-schema dicts - no dependency on pydantic.

A custom widget is selected - in this order - by

1. ``ui:widget`` in the ui-schema naming a registered widget,
2. a registered *path* (merged into the ui-schema as ``ui:widget``, see
   :meth:`WidgetRegistry.apply_paths`),
3. the schema-keyword ``x-widget`` (:data:`SCHEMA_WIDGET_KEY`) of the
   (resolved) schema node,
4. the name of the ``$ref``-definition the node refers to
   (:meth:`WidgetRegistry.register` with ``ref=...``).

If nothing matches, the generic widget of the :class:`WidgetBuilder` is used.

A factory is any callable with the signature of a schema-widget constructor:
``factory(schema, ui_schema, widget_builder, parent=None)`` - so a
``SchemaWidgetMixin``-subclass can be registered directly.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

#: schema-keyword naming the custom widget of a schema node.
SCHEMA_WIDGET_KEY = "x-widget"
#: ui-schema-keyword naming the widget(-variant) of a schema node.
UI_WIDGET_KEY = "ui:widget"

WidgetFactory = Callable[..., Any]
PathLike = Union[str, Tuple[str, ...]]


def _as_path(path: PathLike) -> Tuple[str, ...]:
    return tuple(path.split(".")) if isinstance(path, str) else tuple(path)


def ref_name(ref: Optional[str]) -> Optional[str]:
    """The definition name of a local ``$ref`` (``#/$defs/Name`` -> ``Name``)."""
    if not isinstance(ref, str) or not ref:
        return None
    return ref.rsplit("/", 1)[-1]


class WidgetRegistry:
    """Named custom-widget factories plus the rules selecting them.

    Registries can be layered: :meth:`child` returns a registry that sees all
    registrations of its parent and may add or override its own - e.g. one
    application-wide registry and a context-specific child for a dialog.
    """

    def __init__(self, parent: Optional["WidgetRegistry"] = None) -> None:
        self._parent = parent
        self._factories: Dict[str, WidgetFactory] = {}
        self._refs: Dict[str, str] = {}
        self._paths: Dict[Tuple[str, ...], str] = {}

    # -- layering ---------------------------------------------------------
    @property
    def parent(self) -> Optional["WidgetRegistry"]:
        return self._parent

    def child(self) -> "WidgetRegistry":
        """A new registry layered on top of this one."""
        return type(self)(parent=self)

    def register(self, name: str, factory: WidgetFactory, *,
                 ref: Optional[Union[str, Iterable[str]]] = None,
                 path: Optional[Union[PathLike, Iterable[PathLike]]] = None,
                 replace: bool = False) -> str:
        """Register ``factory`` under ``name``.

        Args:
            name: unique widget name (also usable as ``x-widget``/``ui:widget``).
            factory: widget class or callable ``(schema, ui_schema, builder, parent=None)``.
            ref: definition name(s) (``$defs``-key) rendered by this widget.
            path: field path(s) (``"a.b"``, array items as ``"items"``).
            replace: allow re-registering an existing ``name`` in *this* layer.

        Returns:
            ``name``
        """
        if not callable(factory):
            raise TypeError(f"factory of widget {name!r} is not callable")
        if name in self._factories and not replace:
            raise ValueError(f"widget {name!r} is already registered")
        self._factories[name] = factory
        for item in _iter_values(ref):
            self.register_ref(item, name)
        if path is not None:
            paths = [path] if isinstance(path, (str, tuple)) else list(path)
            for item in paths:
                self.register_path(item, name)
        return name

    def register_ref(self, ref: str, name: str) -> None:
        """Render every ``$ref`` to the definition ``ref`` with widget ``name``."""
        self._refs[ref_name(ref) or ref] = name

    def register_path(self, path: PathLike, name: str) -> None:
        """Render the field ``path`` with widget ``name``."""
        self._paths[_as_path(path)] = name

    def has(self, name: Any) -> bool:
        return self.factory(name) is not None

    def factory(self, name: Any) -> Optional[WidgetFactory]:
        """The factory registered as ``name`` (searching parent layers)."""
        if not isinstance(name, str):
            return None
        if name in self._factories:
            return self._factories[name]
        return self._parent.factory(name) if self._parent is not None else None

    def names(self) -> Tuple[str, ...]:
        """All registered widget names (including parent layers)."""
        own = tuple(self._factories)
        inherited = self._parent.names() if self._parent is not None else ()
        return tuple(dict.fromkeys(own + inherited))

    def _ref_widget(self, name: str) -> Optional[str]:
        if name in self._refs:
            return self._refs[name]
        return self._parent._ref_widget(name) if self._parent is not None else None

    def paths(self) -> Dict[Tuple[str, ...], str]:
        """All path registrations (child layers override their parents)."""
        out = dict(self._parent.paths()) if self._parent is not None else {}
        out.update(self._paths)
        return out

    def resolve(self, schema: Dict, ui_schema: Optional[Dict] = None,
                ref: Optional[str] = None) -> Optional[WidgetFactory]:
        """The custom factory for a schema node or None (generic widget).

        ``schema`` is the *resolved* node, ``ref`` the ``$ref`` it was
        resolved from (if any).
        """
        ui_schema = ui_schema or {}
        for candidate in (ui_schema.get(UI_WIDGET_KEY),
                          schema.get(SCHEMA_WIDGET_KEY) if isinstance(schema, dict) else None):
            factory = self.factory(candidate)
            if factory is not None:
                return factory
        name = ref_name(ref)
        if name is not None:
            return self.factory(self._ref_widget(name))
        return None

    def apply_paths(self, ui_schema: Optional[Dict] = None) -> Dict:
        """Deep-copy ``ui_schema`` and merge the path registrations into it.

        Each registered path gets ``ui:widget = <name>`` unless the ui-schema
        already selects a widget for that node.
        """
        out = deepcopy(ui_schema or {})
        for path, name in sorted(self.paths().items(), key=lambda kv: (len(kv[0]), kv[0])):
            node = out
            for part in path:
                node = node.setdefault(part, {})
            node.setdefault(UI_WIDGET_KEY, name)
        return out


def _iter_values(value) -> Iterable[str]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)
