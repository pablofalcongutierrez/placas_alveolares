"""Cuadratura numérica sobre triángulos.

El integrador es **abstracto**: cualquier regla que cumpla el protocolo
:class:`ReglaCuadratura` puede usarse. Se incluyen dos:

- :class:`Regla1Punto` — baricentro del triángulo; exacta para polinomios de
  grado ≤ 1 (área y momento estático exactos; inercia aproximada).
- :class:`Regla3Puntos` — regla de Gauss de tres puntos; exacta para
  polinomios de grado ≤ 2 (área, momento estático e **inercia exactos**). Es
  la regla por defecto.

El integrador recibe un campo ``Callable[[Punto], float]``, de modo que el
mismo motor servirá para integrar tensiones cuando se incorpore el solver
general por fibras.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from placas_alveolares.domain.mechanics.mallado import Triangulo
from placas_alveolares.domain.model.geometria import Punto


@dataclass(frozen=True, slots=True)
class EvaluacionGauss:
    """Punto de evaluación y peso de una regla de cuadratura.

    Attributes:
        punto: Punto de evaluación en coordenadas de la sección (mm).
        peso: Peso de integración (mm²). Los pesos de una regla suman el área
            del triángulo.
    """

    punto: Punto
    peso: float


class ReglaCuadratura(Protocol):
    """Regla de cuadratura definida sobre un triángulo."""

    def evaluaciones(self, triangulo: Triangulo) -> tuple[EvaluacionGauss, ...]:
        """Evaluaciones de la regla en un triángulo.

        Args:
            triangulo: Triángulo sobre el que se integra.

        Returns:
            Los pares punto-peso de la regla, con pesos en mm².
        """
        ...


@dataclass(frozen=True, slots=True)
class Regla1Punto:
    """Regla de un punto (baricentro), exacta para grado ≤ 1."""

    def evaluaciones(self, triangulo: Triangulo) -> tuple[EvaluacionGauss, ...]:
        """Evalúa la regla en el baricentro del triángulo.

        Args:
            triangulo: Triángulo sobre el que se integra.

        Returns:
            Una única evaluación en el baricentro, con peso igual al área.
        """
        baricentro = _interpolar(triangulo, 1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
        return (EvaluacionGauss(punto=baricentro, peso=_area(triangulo)),)


@dataclass(frozen=True, slots=True)
class Regla3Puntos:
    """Regla de Gauss de tres puntos, exacta para grado ≤ 2."""

    def evaluaciones(self, triangulo: Triangulo) -> tuple[EvaluacionGauss, ...]:
        """Evalúa la regla en los tres puntos de Gauss del triángulo.

        Args:
            triangulo: Triángulo sobre el que se integra.

        Returns:
            Tres evaluaciones con peso igual a un tercio del área.
        """
        peso = _area(triangulo) / 3.0
        coordenadas = (
            (2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0),
            (1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0),
            (1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0),
        )
        return tuple(
            EvaluacionGauss(
                punto=_interpolar(triangulo, la, lb, lc), peso=peso
            )
            for la, lb, lc in coordenadas
        )


REGLA_1_PUNTO: ReglaCuadratura = Regla1Punto()
"""Regla de cuadratura de un punto (baricentro)."""

REGLA_3_PUNTOS: ReglaCuadratura = Regla3Puntos()
"""Regla de cuadratura de tres puntos (por defecto)."""


def _area(triangulo: Triangulo) -> float:
    """Área de un triángulo.

    Args:
        triangulo: Triángulo a medir.

    Returns:
        El área del triángulo (mm²).
    """
    a, b, c = triangulo.a, triangulo.b, triangulo.c
    return abs(
        (b.y - a.y) * (c.z - a.z) - (c.y - a.y) * (b.z - a.z)
    ) / 2.0


def _interpolar(
    triangulo: Triangulo, la: float, lb: float, lc: float
) -> Punto:
    """Interpola un punto a partir de coordenadas baricéntricas.

    Args:
        triangulo: Triángulo de referencia.
        la: Peso baricéntrico del vértice ``a``.
        lb: Peso baricéntrico del vértice ``b``.
        lc: Peso baricéntrico del vértice ``c``.

    Returns:
        El punto interpolado en coordenadas de la sección (mm).
    """
    return Punto(
        y=la * triangulo.a.y + lb * triangulo.b.y + lc * triangulo.c.y,
        z=la * triangulo.a.z + lb * triangulo.b.z + lc * triangulo.c.z,
    )


def integrar(
    malla: tuple[Triangulo, ...],
    campo: Callable[[Punto], float],
    regla: ReglaCuadratura = REGLA_3_PUNTOS,
) -> float:
    """Integra un campo escalar sobre una malla de triángulos.

    Args:
        malla: Triángulos sobre los que integrar.
        campo: Función escalar a integrar, evaluada en coordenadas (mm).
        regla: Regla de cuadratura. Por defecto la de tres puntos.

    Returns:
        La integral del campo sobre la malla (en las unidades del campo por
        mm²).
    """
    return sum(
        evaluacion.peso * campo(evaluacion.punto)
        for triangulo in malla
        for evaluacion in regla.evaluaciones(triangulo)
    )
