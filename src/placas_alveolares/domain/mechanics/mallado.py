"""Mallado en triángulos de regiones de contorno.

El mallado se delega en ``mapbox-earcut``, que triangula polígonos con huecos.
La librería (y ``numpy``) quedan confinados en este módulo: la API pública
devuelve tipos del dominio, de modo que el resto del núcleo no depende de
librerías externas de malla.

La calidad de los triángulos es irrelevante para integrar polinomios: la
cuadratura de Gauss sobre cada triángulo es exacta para el grado que cubre,
independientemente de su forma.
"""

# mapbox-earcut no publica tipos; se aísla aquí su uso.
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

from dataclasses import dataclass

import mapbox_earcut
import numpy as np
from numpy.typing import NDArray

from placas_alveolares.domain.errores import ErrorMallado, GeometriaInvalida
from placas_alveolares.domain.model.geometria import (
    Contorno,
    GeometriaContorno,
    Punto,
)


@dataclass(frozen=True, slots=True)
class Triangulo:
    """Triángulo del mallado de una región.

    Attributes:
        a: Primer vértice.
        b: Segundo vértice.
        c: Tercer vértice.
    """

    a: Punto
    b: Punto
    c: Punto


def _dentro_de(punto: Punto, contorno: Contorno) -> bool:
    """Comprueba si un punto está contenido en un polígono (ray casting).

    Args:
        punto: Punto a comprobar.
        contorno: Polígono de referencia.

    Returns:
        ``True`` si el punto está en el interior del contorno.
    """
    dentro = False
    puntos = contorno.puntos
    for i, p in enumerate(puntos):
        q = puntos[(i + 1) % len(puntos)]
        if (p.z > punto.z) != (q.z > punto.z):
            y_corte = p.y + (punto.z - p.z) * (q.y - p.y) / (q.z - p.z)
            if punto.y < y_corte:
                dentro = not dentro
    return dentro


def mallar(geometria: GeometriaContorno) -> tuple[Triangulo, ...]:
    """Triangula una región de contorno, descontando sus huecos.

    Los huecos deben estar íntegramente contenidos en el contorno exterior y no
    solaparse entre sí; la contención se valida, el solape no.

    Args:
        geometria: Región definida por un contorno exterior y sus huecos.

    Returns:
        Los triángulos del mallado, todos con área positiva.

    Raises:
        GeometriaInvalida: Si un hueco queda fuera del contorno exterior.
        ErrorMallado: Si la triangulación no produce ningún triángulo.
    """
    for hueco in geometria.huecos:
        if not all(_dentro_de(p, geometria.exterior) for p in hueco.puntos):
            raise GeometriaInvalida(
                "Hay un hueco fuera del contorno exterior; revise la geometría."
            )

    puntos: list[Punto] = list(geometria.exterior.puntos)
    finales_anillo: list[int] = [len(puntos)]
    for hueco in geometria.huecos:
        puntos.extend(hueco.puntos)
        finales_anillo.append(len(puntos))

    vertices: NDArray[np.float64] = np.array(
        [(p.y, p.z) for p in puntos], dtype=np.float64
    )
    anillos: NDArray[np.uint32] = np.array(finales_anillo, dtype=np.uint32)
    indices = np.asarray(
        mapbox_earcut.triangulate_float64(vertices, anillos), dtype=np.int64
    )
    if indices.size == 0:
        raise ErrorMallado("La triangulación no ha producido ningún triángulo.")

    return tuple(
        Triangulo(a=puntos[int(i)], b=puntos[int(j)], c=puntos[int(k)])
        for i, j, k in indices.reshape(-1, 3)
    )
