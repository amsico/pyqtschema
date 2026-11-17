"""pyqtschema.pydantic_support: build a form from a model instance, register a widget per model class."""
import sys

from pydantic import BaseModel
from qtpy.QtWidgets import QApplication, QFormLayout

from pyqtschema import CustomObjectWidget
from pyqtschema.pydantic_support import ModelWidgetRegistry, build_widget, to_model


class Address(BaseModel):
    street: str = ""
    city: str = ""


class InvoiceAddress(Address):
    vat_id: str = ""


class Customer(BaseModel):
    name: str = "unknown"
    address: Address = Address()
    invoice: InvoiceAddress = InvoiceAddress()


class AddressWidget(CustomObjectWidget):
    """Compact address editor; extra fields of subclasses stay in the state."""

    def setup_ui(self):
        layout = QFormLayout(self)
        for name in ("street", "city"):
            layout.addRow(self.property_title(name), self.build_field(name))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    registry = ModelWidgetRegistry()
    registry.register_model(Address, AddressWidget)  # also used for InvoiceAddress

    widget = build_widget(Customer(name="ACME"), {"address": {"city": "Berlin"}}, registry=registry)
    widget.on_changed.connect(lambda _state: print(to_model(widget)))
    widget.show()
    app.exec_()
