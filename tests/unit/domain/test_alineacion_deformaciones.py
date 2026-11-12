"""Pruebas del sistema de referencia alineado con la línea neutra."""

from __future__ import annotations

import math

import pytest

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.mechanics.alineacion_deformaciones import (
    PuntoAlineado,
    sistema_referencia_alineado,
)
from placas_alveolares.domain.model.geometria import Punto
from placas_alveolares.domain.state.plano_deformaciones import (
    PlanoDeformaciones,
)


def test_flexion_my_deja_la_linea_neutra_horizontal() -> None:
    """En flexión alrededor de y el giro es nulo y v coincide con z."""
    plano = PlanoDeformaciones(
        eps0=1.0e-3,
        kappa_y=2.0e-6,
        kappa_z=0.0,
    )
    sistema = sistema_referencia_alineado(plano)

    punto = sistema.a_alineado(Punto(y=30.0, z=120.0))

    assert sistema.linea_neutra_definida
    assert sistema.angulo_radianes == pytest.approx(0.0)
    assert punto.u == pytest.approx(30.0)
    assert punto.v == pytest.approx(620.0)
    assert sistema.deformacion_comun(punto.v) == pytest.approx(
        plano.deformacion(30.0, 120.0)
    )


def test_flexion_biaxial_conserva_la_deformacion_en_todo_punto() -> None:
    """La transformación es una rotación y no altera ε(y, z)."""
    plano = PlanoDeformaciones(
        eps0=-4.0e-4,
        kappa_y=1.5e-6,
        kappa_z=-0.8e-6,
    )
    sistema = sistema_referencia_alineado(plano)
    puntos = (
        Punto(y=-200.0, z=-300.0),
        Punto(y=150.0, z=250.0),
        Punto(y=80.0, z=-40.0),
    )

    for punto in puntos:
        alineado = sistema.a_alineado(punto)
        recuperado = sistema.a_seccion(alineado)
        assert sistema.deformacion_comun(alineado.v) == pytest.approx(
            plano.deformacion(punto.y, punto.z)
        )
        assert recuperado.y == pytest.approx(punto.y)
        assert recuperado.z == pytest.approx(punto.z)


def test_linea_neutra_queda_en_v_cero() -> None:
    """La cota alineada de la línea neutra es cero aunque quede fuera."""
    plano = PlanoDeformaciones(
        eps0=-6.0e-4,
        kappa_y=2.0e-6,
        kappa_z=1.0e-6,
    )
    sistema = sistema_referencia_alineado(plano)
    punto = Punto(y=0.0, z=-plano.eps0 / plano.kappa_y)

    alineado = sistema.a_alineado(punto)

    assert alineado.v == pytest.approx(0.0, abs=1.0e-12)


def test_curvatura_nula_no_define_linea_neutra() -> None:
    """Una deformación uniforme conserva los ejes y no tiene línea neutra."""
    plano = PlanoDeformaciones(
        eps0=-3.0e-4,
        kappa_y=0.0,
        kappa_z=0.0,
    )
    sistema = sistema_referencia_alineado(plano)
    punto = sistema.a_alineado(Punto(y=12.0, z=-8.0))

    assert not sistema.linea_neutra_definida
    assert sistema.curvatura == 0.0
    assert sistema.angulo_radianes == pytest.approx(0.0)
    assert sistema.deformacion_comun(punto.v) == pytest.approx(-3.0e-4)


def test_tolerancia_de_curvatura_debe_ser_no_negativa() -> None:
    """Una tolerancia negativa no puede habilitar una línea neutra."""
    with pytest.raises(ErrorValidacion):
        sistema_referencia_alineado(
            PlanoDeformaciones(eps0=0.0, kappa_y=0.0, kappa_z=0.0),
            tolerancia_curvatura=-1.0,
        )


def test_giro_puro_mz_intercambia_los_ejes() -> None:
    """Con κz negativa, la tangente a la línea neutra es z positivo."""
    plano = PlanoDeformaciones(
        eps0=0.0,
        kappa_y=0.0,
        kappa_z=-2.0e-6,
    )
    sistema = sistema_referencia_alineado(plano)
    alineado = sistema.a_alineado(Punto(y=100.0, z=20.0))

    assert sistema.angulo_radianes == pytest.approx(-math.pi / 2.0)
    assert alineado.u == pytest.approx(-20.0)
    assert alineado.v == pytest.approx(100.0)
    assert sistema.a_seccion(PuntoAlineado(u=-20.0, v=100.0)) == Punto(
        y=100.0,
        z=20.0,
    )
