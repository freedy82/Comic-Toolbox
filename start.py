from PyQt6 import QtCore,QtWidgets

from models.const import *
from models.controllers.main_window_controller import MainWindowController
from models.theme import apply_theme

if __name__ == '__main__':
    import sys

    # Qt6 enables high-DPI scaling and high-resolution pixmaps automatically.
    QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QtWidgets.QApplication(sys.argv)
    # Share the native menu font and point size so all controls scale with DPI.
    app.setFont(app.font("QMenuBar"))

    trans = QtCore.QTranslator()
    trans.load(str(RESOURCE_DIR / "languages" / MY_CONFIG.get("general", "language")))
    app.installTranslator(trans)

    theme = MY_CONFIG.get("general", "theme")
    apply_theme(app, theme)

    window = MainWindowController(app,trans)
    window.show()
    sys.exit(app.exec())
