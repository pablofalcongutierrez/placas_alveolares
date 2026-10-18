"""Punto de entrada de la aplicación.

Composition root: aquí se construyen e inyectan las dependencias y se
arranca la interfaz. De momento solo levanta una ventana vacía.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from placas_alveolares.infrastructure.config.settings import obtener_ajustes


class VentanaPrincipal(QMainWindow):
    """Ventana principal (placeholder para el walking skeleton)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("placas_alveolares")
        self.resize(1024, 700)


def principal() -> int:
    """Arranca la aplicación y devuelve el código de salida."""
    ajustes = obtener_ajustes()
    app = QApplication(sys.argv)
    app.setApplicationName("placas_alveolares")
    app.setProperty("nivel_log", ajustes.nivel_log)

    window = VentanaPrincipal()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(principal())
