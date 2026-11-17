"""Smoke-test: every script in ``examples/`` starts without an error.

Each example runs in its own interpreter (it creates its own QApplication)
with the Qt-binding of the current run, on the offscreen platform.  The event
loop is replaced by a single ``processEvents`` so the script returns at once.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
SRC = Path(__file__).resolve().parent.parent / "src"

# replace the blocking event loop, then run the example as `__main__`
BOOTSTRAP = """
import runpy, sys
from qtpy.QtWidgets import QApplication

def _exec(self=None, *args):
    QApplication.processEvents()
    return 0

for name in ("exec", "exec_"):
    if hasattr(QApplication, name):
        setattr(QApplication, name, _exec)

sys.argv = [sys.argv[1]]
runpy.run_path(sys.argv[0], run_name="__main__")
"""

#: examples needing arguments or broken for known reasons: {file name: reason}
SKIP = {
    "examples.py": "no GUI: writes the schema-files to examples/schema/",
    "test.py": "invalid schema: `items` as list (tuple-form of draft 4) is rejected by the latest draft",
}


def _examples():
    for path in sorted(EXAMPLES.glob("*.py")):
        marks = [pytest.mark.skip(reason=SKIP[path.name])] if path.name in SKIP else []
        yield pytest.param(path, id=path.stem, marks=marks)


@pytest.mark.parametrize("path", list(_examples()))
def test_example_runs(path):
    pytest.importorskip("pydantic")
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC), env.get("PYTHONPATH")]))
    result = subprocess.run([sys.executable, "-c", BOOTSTRAP, str(path)], env=env, cwd=EXAMPLES,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-3000:]
