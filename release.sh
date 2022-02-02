#!/bin/bash
rm dist/pyqtschema*.tar.gz
rm dist/pyqtschema*.whl

python -m pip install --upgrade build
python -m build

python3 -m pip install --upgrade twine
python3 -m twine upload --repository testpypi dist/* --verbose --skip-existing

