from pydantic import BaseModel, Field

from pyqtschema import build_example


class UnitValue(BaseModel):
    value: float
    unit: str


class Limits(BaseModel):
    name: str = Field(default='dummy', description='stored in name-column')
    upper: UnitValue
    lower: UnitValue


if __name__ == '__main__':
    build_example(Limits.schema())
