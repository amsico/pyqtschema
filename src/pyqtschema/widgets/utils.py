from typing import Iterator

from PyQt5.QtWidgets import QLayoutItem, QWidget, QLayout


def is_concrete_schema(schema: dict) -> bool:
    return "type" in schema


def iter_layout_items(layout) -> Iterator[QLayoutItem]:
    return (layout.itemAt(i) for i in range(layout.count()))


def iter_layout_widgets(layout: QLayout) -> Iterator[QWidget]:
    return (i.widget() for i in iter_layout_items(layout))
