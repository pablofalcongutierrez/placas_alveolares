"""Pruebas de los coeficientes parciales del Código Estructural."""

from __future__ import annotations

import pytest

from placas_alveolares.norms.ce.coeficientes import (
    COEFICIENTES_CE,
    coeficientes,
    tipos_coeficientes,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance


def test_juego_persistente_o_transitoria() -> None:
    """La situación persistente usa gamma_c = 1,5 y gamma_s = 1,15."""
    juego = coeficientes("CE persistente o transitoria")

    assert juego.gamma_c == pytest.approx(1.5)
    assert juego.gamma_s == pytest.approx(1.15)


def test_juego_accidental() -> None:
    """La situación accidental usa gamma_c = 1,3 y gamma_s = 1,0."""
    juego = coeficientes("CE accidental")

    assert juego.gamma_c == pytest.approx(1.3)
    assert juego.gamma_s == pytest.approx(1.0)


def test_lista_los_juegos_disponibles() -> None:
    """El listado coincide con las claves de la tabla."""
    assert tipos_coeficientes() == tuple(COEFICIENTES_CE)


def test_juego_desconocido() -> None:
    """Un juego que no está en la tabla no es válido."""
    with pytest.raises(CasoFueraDeAlcance):
        coeficientes("CE sísmico")
