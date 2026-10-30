"""Problema de continuación: sistema parametrizado más restricción de arco."""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.numerics.continuacion.restriccion import (
    RestriccionArco,
)
from placas_alveolares.domain.numerics.errores import ErrorProblemaIncompleto
from placas_alveolares.domain.numerics.problema import ProblemaParametrizado


@dataclass(frozen=True, slots=True)
class ProblemaContinuacion:
    """Sistema ``F(u, λ) = 0`` con una restricción de camino.

    Attributes:
        sistema: Sistema parametrizado y sus derivadas.
        restriccion: Restricción de arco que cierra el sistema aumentado.

    Raises:
        ErrorProblemaIncompleto: Si el sistema no aporta ``∂F/∂λ``, necesario
            para construir la dirección tangente de la continuación.
    """

    sistema: ProblemaParametrizado
    restriccion: RestriccionArco

    def __post_init__(self) -> None:
        if self.sistema.derivada_parametro is None:
            raise ErrorProblemaIncompleto(
                "Un problema de continuación necesita que el sistema aporte "
                "derivada_parametro (∂F/∂λ)."
            )
