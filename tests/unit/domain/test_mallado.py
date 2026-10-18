"""Pruebas del mallado en triángulos."""

from __future__ import annotations

import math

import pytest

from placas_alveolares.domain.errores import GeometriaInvalida
from placas_alveolares.domain.mechanics.integracion import REGLA_1_PUNTO, integrar
from placas_alveolares.domain.mechanics.mallado import Triangulo, mallar
from placas_alveolares.domain.model.geometria import (
    Contorno,
    GeometriaContorno,
    Punto,
    circulo,
    rectangulo,
)


def _area_total(malla: tuple[Triangulo, ...]) -> float:
    return integrar(malla, lambda _: 1.0, REGLA_1_PUNTO)


def test_rectangulo_sin_huecos() -> None:
    """Un rectángulo se triangula y conserva su área."""
    malla = mallar(rectangulo(300.0, 500.0))

    assert len(malla) == 2
    assert _area_total(malla) == pytest.approx(150_000.0)


def test_rectangulo_con_hueco() -> None:
    """El mallado descuenta el área del hueco."""
    hueco = Contorno(
        puntos=(
            Punto(y=-50.0, z=150.0),
            Punto(y=50.0, z=150.0),
            Punto(y=50.0, z=350.0),
            Punto(y=-50.0, z=350.0),
        )
    )
    geometria = GeometriaContorno(
        exterior=rectangulo(300.0, 500.0).exterior, huecos=(hueco,)
    )

    malla = mallar(geometria)

    assert _area_total(malla) == pytest.approx(130_000.0)


def test_circulo_poligonizado() -> None:
    """El área del mallado coincide con la del polígono inscrito."""
    n_puntos = 16
    radio = 10.0
    geometria = circulo(Punto(y=0.0, z=0.0), radio=radio, n_puntos=n_puntos)

    malla = mallar(geometria)

    area_poligono = (n_puntos / 2.0) * radio**2 * math.sin(2.0 * math.pi / n_puntos)
    assert len(malla) == n_puntos - 2
    assert _area_total(malla) == pytest.approx(area_poligono)


def test_hueco_fuera_del_contorno() -> None:
    """Un hueco que sale del contorno exterior produce un error."""
    hueco = Contorno(
        puntos=(
            Punto(y=-200.0, z=-100.0),
            Punto(y=200.0, z=-100.0),
            Punto(y=200.0, z=600.0),
            Punto(y=-200.0, z=600.0),
        )
    )
    geometria = GeometriaContorno(
        exterior=rectangulo(300.0, 500.0).exterior, huecos=(hueco,)
    )

    with pytest.raises(GeometriaInvalida):
        mallar(geometria)
