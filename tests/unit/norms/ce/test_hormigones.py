"""Pruebas de las clases de hormigón del Código Estructural."""

from __future__ import annotations

import pytest

from placas_alveolares.norms.ce.materiales.hormigones import (
    FCK_POR_CLASE_CE,
    hormigon,
    tipos_hormigon,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance


@pytest.mark.parametrize(
    ("nombre", "fck", "ecm"),
    [
        ("HA-25", 25.0, 31_477.0),
        ("HA-30", 30.0, 32_834.0),
        ("HA-35", 35.0, 34_076.0),
        ("HA-40", 40.0, 35_220.0),
        ("HA-45", 45.0, 36_284.0),
        ("HA-50", 50.0, 37_279.0),
        ("HA-55", 55.0, 38_215.0),
        ("HA-60", 60.0, 39_100.0),
    ],
)
def test_clases_y_valores_derivados(
    nombre: str, fck: float, ecm: float
) -> None:
    """Cada clase reproduce fck y deriva fcm y Ecm de la Tabla 3.1."""
    material = hormigon(nombre)

    assert material.fck == pytest.approx(fck)
    assert material.fcm == pytest.approx(fck + 8.0)
    assert material.ecm == pytest.approx(ecm, rel=1e-3)


def test_lista_las_clases_disponibles() -> None:
    """El listado coincide con las claves de la tabla."""
    assert tipos_hormigon() == tuple(FCK_POR_CLASE_CE)


def test_hormigon_desconocido() -> None:
    """Una clase que no está en la tabla no es válida."""
    with pytest.raises(CasoFueraDeAlcance):
        hormigon("HA-70")
