"""Geometría de la sección transversal.

La sección se describe en un plano ``y-z`` ligado a la pieza: ``y`` horizontal
positivo hacia la derecha y ``z`` vertical positivo hacia arriba (véase
``docs/specs/001-walking-skeleton-flexion-ce/bases_calculo.md``, §2).

Todos los componentes —incluidos los cordones de pretensado— son regiones
delimitadas por un :class:`Contorno`. Un cordón se representa como un círculo
poligonizado con ``n`` puntos (:func:`circulo`), de modo que el modelo
geométrico es uniforme y el mallado en triángulos no necesita casos especiales.

Las geometrías son **declarativas e independientes**: los componentes pueden
solaparse en el modelo (p. ej. el contorno circular de un cordón dentro del
contorno de hormigón) y es el motor de integración quien resuelve la
superposición. Por ello el área de los contornos se calcula en valor absoluto
(el orden de vértices no importa) y los huecos se restan explícitamente.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_LADOS_MINIMOS = 3
_PUNTOS_CIRCULO_POR_DEFECTO = 16


@dataclass(frozen=True, slots=True)
class Punto:
    """Punto del plano de la sección.

    Attributes:
        y: Coordenada horizontal (mm), positiva hacia la derecha.
        z: Coordenada vertical (mm), positiva hacia arriba.
    """

    y: float
    z: float


@dataclass(frozen=True, slots=True)
class Contorno:
    """Polígono cerrado del plano de la sección.

    El contorno se cierra implícitamente uniendo el último vértice con el
    primero; el sentido de recorrido es indiferente, ya que las áreas se
    calculan en valor absoluto.

    Attributes:
        puntos: Vértices del contorno, en orden.

    Raises:
        ValueError: Si el contorno tiene menos de tres vértices.
    """

    puntos: tuple[Punto, ...]

    def __post_init__(self) -> None:
        if len(self.puntos) < _LADOS_MINIMOS:
            raise ValueError(
                f"Un contorno necesita al menos {_LADOS_MINIMOS} vértices; "
                f"se recibieron {len(self.puntos)}."
            )


@dataclass(frozen=True, slots=True)
class GeometriaContorno:
    """Región material delimitada por un contorno exterior y sus huecos.

    Attributes:
        exterior: Contorno exterior de la región.
        huecos: Huecos interiores a descontar (p. ej. alveolos o vainos), por
            defecto ninguno.
    """

    exterior: Contorno
    huecos: tuple[Contorno, ...] = ()


def rectangulo(
    ancho: float,
    alto: float,
    *,
    y_centro: float = 0.0,
    z_base: float = 0.0,
) -> GeometriaContorno:
    """Construye un contorno rectangular.

    Args:
        ancho: Dimensión horizontal del rectángulo (mm).
        alto: Dimensión vertical del rectángulo (mm).
        y_centro: Coordenada horizontal del centro del rectángulo (mm). Por
            defecto ``0.0``.
        z_base: Cota de la base del rectángulo (mm). Por defecto ``0.0``.

    Returns:
        Una :class:`GeometriaContorno` rectangular sin huecos, centrada en
        ``y = y_centro`` y con base en ``z_base``.
    """
    semiancho = ancho / 2.0
    z_sup = z_base + alto
    y_izq = y_centro - semiancho
    y_der = y_centro + semiancho
    exterior = Contorno(
        puntos=(
            Punto(y=y_izq, z=z_base),
            Punto(y=y_der, z=z_base),
            Punto(y=y_der, z=z_sup),
            Punto(y=y_izq, z=z_sup),
        )
    )
    return GeometriaContorno(exterior=exterior)


def circulo(
    centro: Punto, radio: float, *, n_puntos: int = _PUNTOS_CIRCULO_POR_DEFECTO
) -> GeometriaContorno:
    """Construye un círculo poligonizado con ``n_puntos`` vértices.

    El polígono queda **inscrito** en la circunferencia, por lo que su área
    subestima la del círculo (≈ 2,5 % con el valor por defecto de 16 puntos).
    Este error es de poligonización, no de integración: la cuadratura es exacta
    sobre cada triángulo del mallado.

    Args:
        centro: Centro del círculo (mm).
        radio: Radio del círculo (mm). Debe ser estrictamente positivo.
        n_puntos: Número de vértices del polígono. Por defecto 16.

    Returns:
        Una :class:`GeometriaContorno` circular sin huecos.

    Raises:
        ValueError: Si ``radio`` no es positivo o ``n_puntos`` es menor que 3.
    """
    if radio <= 0.0:
        raise ValueError(f"El radio debe ser positivo; se recibió {radio}.")
    if n_puntos < _LADOS_MINIMOS:
        raise ValueError(
            f"Un círculo necesita al menos {_LADOS_MINIMOS} puntos; "
            f"se recibieron {n_puntos}."
        )
    paso = 2.0 * math.pi / n_puntos
    exterior = Contorno(
        puntos=tuple(
            Punto(
                y=centro.y + radio * math.cos(i * paso),
                z=centro.z + radio * math.sin(i * paso),
            )
            for i in range(n_puntos)
        )
    )
    return GeometriaContorno(exterior=exterior)
