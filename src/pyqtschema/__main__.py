import sys
from pathlib import Path
from typing import Dict, Callable, Optional

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QAction, QScrollArea, QStyle, QMessageBox

from .__version__ import version
from .builder import WidgetBuilder
from .schema import schema_from_json


def _exit(txt: str):
    if txt:
        print(txt)
    exit(1)


class MainWindow(QMainWindow):
    def __init__(self, schema: Dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style = self.style()

        self.menu_file = QMenu('File', self.menuBar())
        self.menu_help = QMenu('Help', self.menuBar())

        load_action = self._create_action('Load data', triggered=self.load_file,
                                          icon=style.standardIcon(QStyle.SP_FileIcon))
        save_action = self._create_action('Save data', triggered=self.save_file,
                                          icon=style.standardIcon(QStyle.SP_DialogSaveButton))
        quit_action = self._create_action('Quit', triggered=self.close,
                                          icon=style.standardIcon(QStyle.SP_BrowserStop))
        for _act in (load_action, save_action, quit_action):
            self.menu_file.addAction(_act)

        about_action = self._create_action('About', triggered=self.about,
                                           icon=style.standardIcon(QStyle.SP_DialogHelpButton))
        self.menu_help.addAction(about_action)

        self.menuBar().addMenu(self.menu_file)
        self.menuBar().addMenu(self.menu_help)

        ui_schema = {}

        builder = WidgetBuilder(schema)
        form = builder.create_form(ui_schema)
        # form.widget.on_changed.connect(lambda d: print(dumps(d, indent=4)))

        widget = QScrollArea()
        widget.setWidget(form)
        widget.setWidgetResizable(True)
        self.setCentralWidget(widget)

    def _create_action(self, text: str, icon: Optional[QIcon] = None, tip: Optional[str] = None,
                       toggled: Optional[Callable] = None, triggered: Optional[Callable] = None, ) -> QAction:
        """Create a QAction"""
        action = QAction(text, self)
        if triggered is not None:
            action.triggered.connect(triggered)
        if toggled is not None:
            action.toggled.connect(toggled)
            action.setCheckable(True)
        if icon is not None:
            action.setIcon(icon)
        if tip is not None:
            action.setToolTip(tip)

        return action

    def load_file(self):
        pass

    def save_file(self):
        pass

    def about(self):
        _text = f'PyQtSchema: {version}'
        QMessageBox.about(self, "pyqtschema", _text)


def run(path_schema: Path, *qt_args):
    schema = schema_from_json(path)

    app = QApplication(*qt_args)

    main = MainWindow(schema)
    main.setWindowTitle(str(path_schema))
    main.show()

    app.exec()


if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) == 0:
        _exit('Specify a path to a json-schema')

    path = Path(args[0])

    _args = [] if len(args) == 1 else args[1:]

    run(path, _args)
