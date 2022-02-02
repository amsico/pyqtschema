#!/bin/bash

rm dist/pyqtschema*.tar.gz
rm dist/pyqtschema*.whl

python -m pip install --upgrade build
python -m pip install --upgrade twine

python -m build

if [ "$1" = "pypi" ]; then
  python -m twine upload --repository pypi dist/* --verbose --skip-existing
else
  python -m twine upload --repository testpypi dist/* --verbose --skip-existing
fi
