"""Pruebas del tipo temporal de las fases."""

from __future__ import annotations

import math

import pytest

from placas_alveolares.domain.errores import FaseInvalida
from placas_alveolares.domain.model.tiempo import Tiempo, UnidadTiempo


def test_tiempo_por_defecto_en_dias() -> None:
    """Sin unidad explícita, el valor se interpreta en días."""
    assert Tiempo(2.0).dias == pytest.approx(2.0)


def test_tiempo_en_horas_se_convierte_a_dias() -> None:
    """Las horas se convierten al comparar y calcular."""
    assert Tiempo(6.0, UnidadTiempo.HORAS).dias == pytest.approx(0.25)
    assert Tiempo(24.0, UnidadTiempo.HORAS).dias == pytest.approx(1.0)


@pytest.mark.parametrize("valor", [-1.0, math.nan, math.inf, -math.inf])
def test_tiempo_invalido(valor: float) -> None:
    """El tiempo debe ser finito y no negativo."""
    with pytest.raises(FaseInvalida):
        Tiempo(valor)
