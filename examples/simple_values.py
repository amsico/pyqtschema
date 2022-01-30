from pydantic import BaseModel, Field

from pyqtschema import build_example


class Simple(BaseModel):
    string: str = Field()
    boolean: bool = Field(default=True)
    integer: int = Field(default=2)
    number: float = Field(default=2.2)


if __name__ == '__main__':
    build_example(Simple.schema())
