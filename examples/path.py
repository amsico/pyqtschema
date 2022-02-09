from pathlib import Path

from pydantic import BaseModel, DirectoryPath

from pyqtschema import build_example


class FileSystem(BaseModel):
    my_file: Path
    my_dir: DirectoryPath


if __name__ == '__main__':
    build_example(FileSystem.schema())
