from typing import Union

from pydantic import BaseModel, Field

from pyqtschema import build_example


class Linux(BaseModel):
    distro: str = 'distro'
    version: str = 'version'


class Windows(BaseModel):
    Version: int = 10


class Selection(BaseModel):
    system: Union[Linux, Windows] = Field(default=Windows())

    class Config:
        extra = 'forbid'


if __name__ == '__main__':
    build_example(Selection.schema())
