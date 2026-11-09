"""Pruebas del plano de deformaciones."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)


def test_deformacion_en_una_fibra() -> None:
    """La deformación combina el axil y las dos curvaturas."""
    plano = PlanoDeformaciones(
        eps0=1.0e-4, kappa_y=2.0e-6, kappa_z=-3.0e-6
    )

    assert plano.deformacion(y=10.0, z=20.0) == pytest.approx(1.7e-4)


def test_suma_de_planos() -> None:
    """La suma de planos es componente a componente."""
    primero = PlanoDeformaciones(
        eps0=1.0e-4, kappa_y=2.0e-6, kappa_z=-3.0e-6
    )
    segundo = PlanoDeformaciones(
        eps0=5.0e-5, kappa_y=-1.0e-6, kappa_z=4.0e-6
    )

    suma = primero + segundo

    assert suma.eps0 == pytest.approx(1.5e-4)
    assert suma.kappa_y == pytest.approx(1.0e-6)
    assert suma.kappa_z == pytest.approx(1.0e-6)


def test_plano_nulo_es_neutro() -> None:
    """El plano nulo no altera la deformación de una fibra."""
    plano = PlanoDeformaciones(
        eps0=1.0e-4, kappa_y=2.0e-6, kappa_z=-3.0e-6
    )

    total = PLANO_NULO + plano

    assert total == plano
    assert plano.deformacion(y=0.0, z=0.0) == pytest.approx(1.0e-4)
