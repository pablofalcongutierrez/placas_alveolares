"""Pruebas del objeto de valor de coeficientes parciales de seguridad."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import CoeficientesInvalidos
from placas_alveolares.domain.value_objects.coeficientes_parciales import (
    CoeficientesParciales,
)


def test_crea_un_juego_de_coeficientes() -> None:
    """Los coeficientes positivos se conservan sin transformación."""
    coeficientes = CoeficientesParciales(gamma_c=1.5, gamma_s=1.15)

    assert coeficientes.gamma_c == pytest.approx(1.5)
    assert coeficientes.gamma_s == pytest.approx(1.15)


@pytest.mark.parametrize(
    ("gamma_c", "gamma_s"),
    [(0.0, 1.15), (-1.5, 1.15), (1.5, 0.0), (1.5, -1.15)],
)
def test_exige_coeficientes_positivos(gamma_c: float, gamma_s: float) -> None:
    """Un coeficiente nulo o negativo no es válido."""
    with pytest.raises(CoeficientesInvalidos):
        CoeficientesParciales(gamma_c=gamma_c, gamma_s=gamma_s)
