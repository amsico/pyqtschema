"""Run the test-suite once per installed Qt binding.

``pyqtschema`` is built on QtPy, so the same tests run against every Qt
binding. However, a single pytest process can only exercise one binding:
pytest-qt and QtPy each pick a binding through their own environment
variable (``PYTEST_QT_API`` and ``QT_API``), and the binding modules cannot
be swapped in a running interpreter.

This ``conftest`` adds an opt-in ``--all-backends`` flag: when given, pytest
re-invokes itself once per *installed* binding (each run in its own
subprocess, so every run gets a fresh interpreter and its own QApplication)
and reports a combined result. Runs without the flag are completely
untouched, and runs that already have a binding selected via the environment
(or by tox) never orchestrate.
"""

import os
import subprocess
import sys

import pytest

# (importable module name, QtPy/pytest-qt API name)
# pytest-qt 4.x supports PySide6, PyQt6 and PyQt5.
BACKENDS = [
    ("PyQt5", "pyqt5"),
    ("PyQt6", "pyqt6"),
    ("PySide6", "pyside6"),
]


def _importable(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def _installed_backends():
    return [api for module, api in BACKENDS if _importable(module)]


def pytest_addoption(parser):
    parser.addoption(
        "--all-backends",
        action="store_true",
        help="run the test-suite once per installed Qt binding",
    )


def pytest_configure(config):
    if not config.getoption("--all-backends"):
        return

    # Never orchestrate inside a spawned run or when a binding was already
    # selected explicitly (e.g. by tox or an environment variable).
    if os.environ.get("PYTEST_QT_API") or os.environ.get("QT_API"):
        return
    if os.environ.get("PYQTEST_BACKEND_RUN") == "1":
        return

    backends = _installed_backends()
    if not backends:
        pytest.exit("--all-backends: no Qt binding installed", returncode=1)

    failed = []
    for api in backends:
        env = dict(os.environ)
        env["PYQTEST_BACKEND_RUN"] = "1"
        env["QT_API"] = api
        env["PYTEST_QT_API"] = api

        print(f"\n>>> Running the test-suite against backend: {api}")
        code = subprocess.run(
            [sys.executable, "-m", "pytest", *sys.argv[1:]], env=env
        ).returncode
        status = "OK" if code == 0 else "FAILED"
        print(f">>> Backend {api}: {status}")
        if code != 0:
            failed.append(api)

    if failed:
        pytest.exit(f"--all-backends: failed backends: {failed}", returncode=1)
    pytest.exit("--all-backends: all backends passed", returncode=0)
