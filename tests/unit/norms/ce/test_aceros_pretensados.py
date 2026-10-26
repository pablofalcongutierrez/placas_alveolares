"""Pruebas de los cordones de pretensado del Código Estructural."""

from __future__ import annotations

import pytest

from placas_alveolares.norms.ce.materiales.aceros_pretensados import (
    ACEROS_PRETENSADOS_CE,
    acero_pretensado,
    tipos_acero_pretensado,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance


@pytest.mark.parametrize("nombre", list(ACEROS_PRETENSADOS_CE))
def test_cordones_tienen_fpk_y_ep(nombre: str) -> None:
    """Cada cordón reproduce su fpk y el módulo habitual."""
    material = acero_pretensado(nombre)

    assert material.fpk == pytest.approx(
        ACEROS_PRETENSADOS_CE[nombre].fpk
    )
    assert material.ep == pytest.approx(195_000.0)


@pytest.mark.parametrize(
    ("nombre", "fpk"),
    [
        ("Y 1670 S7", 1_670.0),
        ("Y 1770 S7", 1_770.0),
        ("Y 1860 S7", 1_860.0),
        ("Y 1960 S7", 1_960.0),
    ],
)
def test_valores_de_cada_cordon(nombre: str, fpk: float) -> None:
    """Las designaciones de la tabla se resuelven con su fpk."""
    assert acero_pretensado(nombre).fpk == pytest.approx(fpk)


def test_lista_los_cordones_disponibles() -> None:
    """El listado coincide con las claves de la tabla."""
    assert tipos_acero_pretensado() == tuple(ACEROS_PRETENSADOS_CE)


def test_cordon_desconocido() -> None:
    """Una designación que no está en la tabla no es válida."""
    with pytest.raises(CasoFueraDeAlcance):
        acero_pretensado("Y 2000 S7")
