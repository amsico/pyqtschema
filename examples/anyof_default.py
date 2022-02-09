from typing import Union

from pydantic import BaseModel

from pyqtschema import build_example


class AnyOfDefault(BaseModel):
    other_default: Union[str, int] = 1


if __name__ == '__main__':
    build_example(AnyOfDefault.schema())
