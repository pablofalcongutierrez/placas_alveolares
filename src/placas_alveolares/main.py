"""Punto de entrada de la aplicación.

Composition root: aquí se construyen e inyectan las dependencias y se
arranca la interfaz. De momento solo levanta una ventana vacía.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from placas_alveolares.infrastructure.config.settings import get_settings


class MainWindow(QMainWindow):
    """Ventana principal (placeholder para el walking skeleton)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("placas_alveolares")
        self.resize(1024, 700)


def main() -> int:
    """Arranca la aplicación y devuelve el código de salida."""
    settings = get_settings()
    app = QApplication(sys.argv)
    app.setApplicationName("placas_alveolares")
    app.setProperty("log_level", settings.log_level)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
