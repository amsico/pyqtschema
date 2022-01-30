from typing import Union

from pydantic import BaseModel

from pyqtschema import build_example


class SimpleAnyOf(BaseModel):
    value: Union[str, int]


if __name__ == '__main__':
    build_example(SimpleAnyOf.schema())
