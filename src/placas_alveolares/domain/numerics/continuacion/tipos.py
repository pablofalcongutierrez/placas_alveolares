"""Tipos del solver de continuación.

Un solver de continuación no resuelve un único ``F(x) = 0``: recorre una
trayectoria de estados ``(u, λ)`` que satisfacen ``F(u, λ) = 0`` y una
restricción de arco. El factor de carga ``λ`` es una incógnita más, no un
parámetro fijo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from placas_alveolares.domain.numerics.errores import (
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorOpcionesInvalidas,
)
from placas_alveolares.domain.numerics.resultado import IteracionSolver


@dataclass(frozen=True, slots=True)
class EstadoContinuacion:
    """Estado de equilibrio ``(u, λ)`` de una trayectoria.

    Attributes:
        u: Vector de desplazamientos o deformaciones generalizadas.
        parametro: Factor de carga ``λ``.
    """

    u: tuple[float, ...]
    parametro: float

    def __post_init__(self) -> None:
        if not self.u:
            raise ErrorDimensionesInvalidas(
                "El estado de continuación necesita al menos una componente "
                "en u."
            )
        if not all(math.isfinite(componente) for componente in self.u):
            raise ErrorEvaluacionNoFinita(
                "El vector u del estado de continuación contiene valores no "
                "finitos."
            )
        if not math.isfinite(self.parametro):
            raise ErrorEvaluacionNoFinita(
                "El parámetro del estado de continuación no es finito."
            )


@dataclass(frozen=True, slots=True)
class OpcionesContinuacion:
    """Opciones del algoritmo de continuación.

    El radio de arco ``Δs`` puede adaptarse entre pasos. La restricción
    esférica mezcla ``u`` y ``λ``; por eso el peso ``ψ`` de la restricción
    debe elegirse de forma coherente con las unidades de ``u``.

    Attributes:
        radio_inicial: Radio de arco del primer paso.
        radio_minimo: Radio mínimo antes de detener la continuación.
        radio_maximo: Radio máximo permitido.
        max_pasos: Número máximo de pasos de continuación.
        tolerancia_arco: Tolerancia para el residuo de la restricción.
        parametro_objetivo: Valor de ``λ`` en el que se desea detener. Si es
            ``None``, se detiene por ``max_pasos`` o ``radio_minimo``.
        adaptar_radio: Si se adapta el radio según la dificultad del paso.
        factor_crecimiento: Factor de crecimiento del radio.
        factor_reduccion: Factor de reducción del radio.
    """

    radio_inicial: float = 0.1
    radio_minimo: float = 1e-6
    radio_maximo: float = 1.0
    max_pasos: int = 100
    tolerancia_arco: float = 1e-9
    parametro_objetivo: float | None = None
    adaptar_radio: bool = True
    factor_crecimiento: float = 1.5
    factor_reduccion: float = 0.5

    def __post_init__(self) -> None:
        for nombre, valor in (
            ("radio_inicial", self.radio_inicial),
            ("radio_minimo", self.radio_minimo),
            ("radio_maximo", self.radio_maximo),
            ("tolerancia_arco", self.tolerancia_arco),
            ("factor_crecimiento", self.factor_crecimiento),
            ("factor_reduccion", self.factor_reduccion),
        ):
            if not math.isfinite(valor) or valor <= 0.0:
                raise ErrorOpcionesInvalidas(
                    f"{nombre} debe ser un número finito positivo."
                )
        if not (
            self.radio_minimo
            <= self.radio_inicial
            <= self.radio_maximo
        ):
            raise ErrorOpcionesInvalidas(
                "Debe cumplirse radio_minimo ≤ radio_inicial ≤ radio_maximo."
            )
        if self.max_pasos < 1:
            raise ErrorOpcionesInvalidas(
                "max_pasos debe ser al menos 1."
            )
        if self.factor_crecimiento < 1.0:
            raise ErrorOpcionesInvalidas(
                "factor_crecimiento debe ser al menos 1."
            )
        if not 0.0 < self.factor_reduccion < 1.0:
            raise ErrorOpcionesInvalidas(
                "factor_reduccion debe estar estrictamente entre 0 y 1."
            )
        if self.parametro_objetivo is not None and not math.isfinite(
            self.parametro_objetivo
        ):
            raise ErrorOpcionesInvalidas(
                "parametro_objetivo debe ser finito o None."
            )


class MotivoParada(StrEnum):
    """Motivo por el que finaliza una continuación."""

    MAX_PASOS = "max_pasos"
    PARAMETRO_OBJETIVO = "parametro_objetivo"
    RADIO_MINIMO = "radio_minimo"


@dataclass(frozen=True, slots=True)
class PasoContinuacion:
    """Estado convergido tras un paso de continuación.

    Attributes:
        indice: Número de paso, empezando en 1.
        estado: Estado ``(u, λ)`` convergido.
        incremento_arco: Radio de arco utilizado en el paso.
        iteraciones_corrector: Iteraciones del corrector no lineal.
        historial_corrector: Historial de esas iteraciones.
        norma_residuo: Norma del residuo ``F(u, λ)``.
        norma_restriccion: Valor absoluto del residuo de la restricción.
    """

    indice: int
    estado: EstadoContinuacion
    incremento_arco: float
    iteraciones_corrector: int
    historial_corrector: tuple[IteracionSolver, ...]
    norma_residuo: float
    norma_restriccion: float


@dataclass(frozen=True, slots=True)
class ResultadoContinuacion:
    """Trayectoria recorrida por un solver de continuación.

    Attributes:
        pasos: Estados convergidos, en orden.
        motivo_parada: Motivo por el que finalizó la continuación.
    """

    pasos: tuple[PasoContinuacion, ...]
    motivo_parada: MotivoParada
