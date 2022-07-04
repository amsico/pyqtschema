from enum import Enum

from pydantic import BaseModel

from pyqtschema import build_example


class Units(Enum):
    none = '1'
    meter = 'm'
    seconds = 's'


class UnitValue(BaseModel):
    value: float
    unit: Units


if __name__ == '__main__':
    build_example(UnitValue.schema())
