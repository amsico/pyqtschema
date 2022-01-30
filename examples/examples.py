from enum import Enum
from pathlib import Path
from typing import Union, List

from pydantic import BaseModel, Field


class Units(Enum):
    none = '1'
    meter = 'm'
    seconds = 's'


class UnitValue(BaseModel):
    value: float
    unit: Units


class Limits(BaseModel):
    name: str = Field(default='dummy', description='stored in name-column')
    upper: UnitValue
    lower: UnitValue


class Simple(BaseModel):
    string: str = Field()
    boolean: bool = Field(default=True)
    integer: int = Field(default=2)
    number: float = Field(default=2.2)


class SimpleList(BaseModel):
    string: str = Field()
    boolean: List[bool] = Field()
    integer: List[int] = Field()
    number: List[float] = Field()


class Command1(BaseModel):
    number: int = 1


class Command2(BaseModel):
    number: float = 2
    window: int = 5


class Action(BaseModel):
    command: Union[Command1, Command2]


class SubComplex(BaseModel):
    limits: Limits
    action: Action


class Complex(BaseModel):
    a_lot: List[SubComplex]
    choose: Union[Action, Limits]


class SimpleAnyOf(BaseModel):
    value: Union[str, int]


def write(filename: str, mod: BaseModel, indent=2):
    path = Path(__file__).parent.joinpath('schema')
    path.mkdir(exist_ok=True)
    path = path.joinpath(filename)
    schema = mod.schema_json(indent=indent)
    with open(path, 'w') as OUT:
        OUT.write(schema)


if __name__ == '__main__':
    write('simple_values.json', Simple)
    write('simple_ref.json', Limits)
    write('simple_one_of.json', SimpleAnyOf)
    write('one_of_ref.json', Action)
    write('complex.json', Complex)
