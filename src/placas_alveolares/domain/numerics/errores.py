"""Errores tipados de los solvers numéricos.

Todos derivan de :class:`ErrorCalculo`, de modo que las capas exteriores
puedan capturar un único tipo raíz. El paquete numérico es independiente de la
física: no conoce mecánica, normas ni el modelo estructural.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from placas_alveolares.domain.errores import ErrorCalculo

if TYPE_CHECKING:
    from placas_alveolares.domain.numerics.continuacion.tipos import (
        ResultadoContinuacion,
    )
    from placas_alveolares.domain.numerics.resultado import ResultadoSolver


class ErrorSolver(ErrorCalculo):
    """Error raíz de los solvers numéricos."""


class ErrorOpcionesInvalidas(ErrorSolver):
    """Configuración de un solver no válida."""


class ErrorDimensionesInvalidas(ErrorSolver):
    """Dimensiones incompatibles entre vectores, matrices o estados."""


class ErrorEvaluacionNoFinita(ErrorSolver):
    """Un residuo, Jacobiano o vector contiene NaN o infinito."""


class ErrorProblemaIncompleto(ErrorSolver):
    """El problema no aporta los datos que el solver necesita."""


class ErrorJacobianoSingular(ErrorSolver):
    """El Jacobiano es singular o el sistema lineal no tiene solución finita.

    Attributes:
        iteracion: Iteración de Newton en la que se detectó el fallo.
        x: Estado en el que se evaluó el Jacobiano.
        detalle: Información adicional del fallo.
    """

    def __init__(
        self,
        iteracion: int,
        x: tuple[float, ...],
        detalle: str = "",
    ) -> None:
        self.iteracion = iteracion
        self.x = x
        self.detalle = detalle
        mensaje = f"Jacobiano singular en la iteración {iteracion}."
        if detalle:
            mensaje = f"{mensaje} {detalle}"
        super().__init__(mensaje)


class ErrorNoConvergencia(ErrorSolver):
    """El solver agotó las iteraciones o se estancó sin alcanzar la tolerancia.

    Attributes:
        resultado: Resultado parcial con el historial de iteraciones.
        motivo: Descripción legible del motivo de parada.
    """

    def __init__(self, resultado: ResultadoSolver, motivo: str) -> None:
        self.resultado = resultado
        self.motivo = motivo
        super().__init__(motivo)


class ErrorContinuacion(ErrorSolver):
    """Error raíz de los solvers de continuación."""


class ErrorNoConvergenciaContinuacion(ErrorContinuacion):
    """Un paso de continuación no convergió.

    Attributes:
        resultado: Trayectoria parcial recorrida hasta el fallo.
        motivo: Descripción legible del motivo.
    """

    def __init__(self, resultado: ResultadoContinuacion, motivo: str) -> None:
        self.resultado = resultado
        self.motivo = motivo
        super().__init__(motivo)
