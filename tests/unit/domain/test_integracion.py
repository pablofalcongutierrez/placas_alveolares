"""Pruebas de la cuadratura numérica sobre triángulos."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.mechanics.integracion import (
    REGLA_1_PUNTO,
    REGLA_3_PUNTOS,
    ReglaCuadratura,
    integrar,
)
from placas_alveolares.domain.mechanics.mallado import Triangulo, mallar
from placas_alveolares.domain.model.geometria import Punto, rectangulo


def _malla_rectangulo() -> tuple[Triangulo, ...]:
    return mallar(rectangulo(300.0, 500.0, z_base=0.0))


@pytest.mark.parametrize("regla", [REGLA_1_PUNTO, REGLA_3_PUNTOS])
def test_los_pesos_suman_el_area(regla: ReglaCuadratura) -> None:
    """La suma de pesos de una regla es el área del triángulo."""
    triangulo = Triangulo(
        a=Punto(y=0.0, z=0.0),
        b=Punto(y=2.0, z=0.0),
        c=Punto(y=0.0, z=3.0),
    )

    suma = sum(e.peso for e in regla.evaluaciones(triangulo))

    assert suma == pytest.approx(3.0)


def test_integral_de_constante_es_el_area() -> None:
    """Integrar la unidad devuelve el área de la malla."""
    malla = _malla_rectangulo()

    assert integrar(malla, lambda _: 1.0) == pytest.approx(150_000.0)


def test_momento_estatico_exacto() -> None:
    """La integral de z es el momento estático de la sección."""
    malla = _malla_rectangulo()

    assert integrar(malla, lambda punto: punto.z) == pytest.approx(
        150_000.0 * 250.0
    )


def test_momento_de_segundo_orden_exacto() -> None:
    """La regla de tres puntos integra z² de forma exacta."""
    malla = _malla_rectangulo()

    assert integrar(malla, lambda punto: punto.z**2) == pytest.approx(
        300.0 * 500.0**3 / 3.0
    )


def test_segundo_momento_respecto_a_z() -> None:
    """La integral de y² es el momento de inercia respecto a z."""
    malla = _malla_rectangulo()

    assert integrar(malla, lambda punto: punto.y**2) == pytest.approx(
        500.0 * 300.0**3 / 12.0
    )


def test_producto_de_inercia_nulo_por_simetria() -> None:
    """Una sección simétrica respecto a ambos ejes no tiene producto de inercia."""
    malla = _malla_rectangulo()

    assert integrar(malla, lambda punto: punto.y * punto.z) == pytest.approx(
        0.0, abs=1e-6
    )


def test_momentos_con_rectangulo_descentrado() -> None:
    """Un rectángulo desplazado en y conserva su producto de inercia nulo."""
    malla = mallar(rectangulo(300.0, 500.0, y_centro=100.0))

    assert integrar(malla, lambda punto: punto.y) == pytest.approx(
        150_000.0 * 100.0
    )
    assert integrar(malla, lambda punto: punto.y * punto.z) == pytest.approx(
        150_000.0 * 100.0 * 250.0
    )


def test_regla_de_un_punto_aproxima_el_momento_de_segundo_orden() -> None:
    """Con un solo punto, z² no se integra exactamente."""
    malla = _malla_rectangulo()

    aproximada = integrar(malla, lambda punto: punto.z**2, REGLA_1_PUNTO)
    exacta = integrar(malla, lambda punto: punto.z**2)

    assert aproximada < exacta
