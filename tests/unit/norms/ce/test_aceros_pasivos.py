"""Pruebas de los aceros pasivos del Código Estructural (Tabla 34.2.a)."""

from __future__ import annotations

import pytest

from placas_alveolares.norms.ce.materiales.aceros_pasivos import (
    acero_pasivo,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance


@pytest.mark.parametrize(
    ("nombre", "fyk", "ftk", "eps_uk"),
    [
        ("B 400 S", 400.0, 440.0, 0.050),
        ("B 500 S", 500.0, 550.0, 0.050),
        ("B 400 SD", 400.0, 480.0, 0.075),
        ("B 500 SD", 500.0, 575.0, 0.075),
    ],
)
def test_valores_caracteristicos_en_barra(
    nombre: str,
    fyk: float,
    ftk: float,
    eps_uk: float,
) -> None:
    """Cada tipo reproduce los mínimos de barra de la Tabla 34.2.a."""
    acero = acero_pasivo(nombre)

    assert acero.fyk == pytest.approx(fyk)
    assert acero.ftk == pytest.approx(ftk)
    assert acero.es == pytest.approx(200_000.0)
    assert acero.eps_uk == pytest.approx(eps_uk)


def test_acero_pasivo_desconocido() -> None:
    """Una designación que no está en la tabla no es válida."""
    with pytest.raises(CasoFueraDeAlcance):
        acero_pasivo("B 450 S")
