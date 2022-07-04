from pathlib import Path
from typing import Union

from pydantic import BaseModel, Field

from pyqtschema import build_example


class UnionIssue(BaseModel):
    # see issue #13:
    #   the str-schema is {type: string}
    #   the Path-schema is {type: string, format=path}
    output: Union[str, Path] = Field(default=None)


if __name__ == '__main__':
    print(UnionIssue.schema())
    build_example(UnionIssue.schema())
