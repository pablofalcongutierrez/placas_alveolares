"""Pruebas de las propiedades geométricas de la sección."""

from __future__ import annotations

import math

import pytest

from placas_alveolares.domain.mechanics.integracion import REGLA_1_PUNTO
from placas_alveolares.domain.mechanics.propiedades_seccion import (
    propiedades_geometricas,
)
from placas_alveolares.domain.model.geometria import (
    Contorno,
    GeometriaContorno,
    Punto,
    circulo,
    rectangulo,
)


def test_rectangulo_300x500() -> None:
    """Rectángulo 300×500 con base en z=0."""
    propiedades = propiedades_geometricas(rectangulo(300.0, 500.0, z_base=0.0))

    assert propiedades.area == pytest.approx(150_000.0)
    assert propiedades.y_cdg == pytest.approx(0.0)
    assert propiedades.z_cdg == pytest.approx(250.0)
    assert propiedades.i_y == pytest.approx(3.125e9)
    assert propiedades.i_z == pytest.approx(500.0 * 300.0**3 / 12.0)
    assert propiedades.i_yz == pytest.approx(0.0)


def test_rectangulo_centrado_en_origen() -> None:
    """Un rectángulo centrado en el origen tiene cdg en (0, 0)."""
    geometria = rectangulo(300.0, 500.0, z_base=-250.0)

    propiedades = propiedades_geometricas(geometria)

    assert propiedades.y_cdg == pytest.approx(0.0)
    assert propiedades.z_cdg == pytest.approx(0.0)
    assert propiedades.i_y == pytest.approx(3.125e9)
    assert propiedades.i_z == pytest.approx(1.125e9)


def test_rectangulo_descentrado_en_y() -> None:
    """Un rectángulo desplazado en y traslada el centro de gravedad."""
    geometria = rectangulo(300.0, 500.0, y_centro=100.0)

    propiedades = propiedades_geometricas(geometria)

    assert propiedades.y_cdg == pytest.approx(100.0)
    assert propiedades.z_cdg == pytest.approx(250.0)
    assert propiedades.i_y == pytest.approx(3.125e9)
    assert propiedades.i_z == pytest.approx(1.125e9)
    assert propiedades.i_yz == pytest.approx(0.0, abs=1e-6)


def test_region_con_hueco_centrado() -> None:
    """El área del hueco se descuenta y la inercia es la diferencia."""
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

    propiedades = propiedades_geometricas(geometria)

    assert propiedades.area == pytest.approx(130_000.0)
    assert propiedades.z_cdg == pytest.approx(250.0)
    assert propiedades.i_y == pytest.approx((300.0 * 500.0**3 - 100.0 * 200.0**3) / 12.0)
    assert propiedades.i_z == pytest.approx((500.0 * 300.0**3 - 200.0 * 100.0**3) / 12.0)
    assert propiedades.i_yz == pytest.approx(0.0, abs=1e-6)


def test_hueco_fuera_del_contorno() -> None:
    """Un hueco que no cabe en el contorno exterior no es válido."""
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

    with pytest.raises(ValueError):
        propiedades_geometricas(geometria)


def test_seccion_en_l_tiene_producto_de_inercia() -> None:
    """Una sección asimétrica en L presenta producto de inercia no nulo."""
    exterior = Contorno(
        puntos=(
            Punto(y=0.0, z=0.0),
            Punto(y=200.0, z=0.0),
            Punto(y=200.0, z=100.0),
            Punto(y=100.0, z=100.0),
            Punto(y=100.0, z=300.0),
            Punto(y=0.0, z=300.0),
        )
    )

    propiedades = propiedades_geometricas(GeometriaContorno(exterior=exterior))

    assert propiedades.area == pytest.approx(40_000.0)
    assert propiedades.y_cdg == pytest.approx(75.0)
    assert propiedades.z_cdg == pytest.approx(125.0)
    assert propiedades.i_y == pytest.approx(3.083333e8)
    assert propiedades.i_z == pytest.approx(1.083333e8)
    assert propiedades.i_yz == pytest.approx(-7.5e7)


def test_circulo_poligonizado() -> None:
    """Las propiedades del círculo tienden a las del círculo teórico."""
    radio = 20.0
    geometria = circulo(Punto(y=0.0, z=0.0), radio=radio, n_puntos=64)

    propiedades = propiedades_geometricas(geometria)

    assert propiedades.area == pytest.approx(math.pi * radio**2, rel=2e-3)
    assert propiedades.y_cdg == pytest.approx(0.0, abs=1e-9)
    assert propiedades.z_cdg == pytest.approx(0.0, abs=1e-9)
    assert propiedades.i_y == pytest.approx(math.pi * radio**4 / 4.0, rel=5e-3)
    assert propiedades.i_z == pytest.approx(math.pi * radio**4 / 4.0, rel=5e-3)
    assert propiedades.i_yz == pytest.approx(0.0, abs=1e-6)


def test_regla_de_un_punto_no_es_exacta_para_inercia() -> None:
    """Con un punto, área y cdg son exactos, pero la inercia no."""
    geometria = rectangulo(300.0, 500.0, z_base=0.0)

    exactas = propiedades_geometricas(geometria)
    aproximadas = propiedades_geometricas(geometria, regla=REGLA_1_PUNTO)

    assert aproximadas.area == pytest.approx(exactas.area)
    assert aproximadas.y_cdg == pytest.approx(exactas.y_cdg)
    assert aproximadas.z_cdg == pytest.approx(exactas.z_cdg)
    assert aproximadas.i_y < exactas.i_y
    assert aproximadas.i_z < exactas.i_z
