from typing import Any

import pytest
from PyQt5.QtWidgets import QWidget

from pyqtschema.builder_opt import IBuilder
from pyqtschema.widgets import SchemaWidgetMixin
from pyqtschema.widgets.base import state_property


class MockWidget(SchemaWidgetMixin, QWidget):
    """ Mock widget """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = ''

    @state_property
    def state(self) -> Any:
        return self._value

    @state.setter
    def state(self, state: Any):
        self._value = state


class MockBuilder(IBuilder):
    def create_widget(self, schema: dict, ui_schema: dict, state=None) -> SchemaWidgetMixin:
        return MockWidget()


@pytest.fixture(scope="module")
def builder():
    return MockBuilder()
