"""Pruebas de las leyes constitutivas del acero pasivo de la familia eurocódigo."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from placas_alveolares.domain.mechanics.generic_laws import LeyElastoplastica
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.model.materiales import AceroArmadura
from placas_alveolares.norms.errores import CasoFueraDeAlcance
from placas_alveolares.norms.eurocode.laws import (
    LeyBilinealEndurecida,
    ley_acero_pasivo_bilineal,
    ley_acero_pasivo_endurecida,
)

ACERO_B500S = AceroArmadura(
    fyk=500.0,
    ftk=550.0,
    es=200_000.0,
    eps_uk=0.075,
)
"""Acero B500S de referencia."""

GAMMA_S = 1.15
"""Coeficiente parcial del acero."""

FYD = ACERO_B500S.fyk / GAMMA_S
"""Límite elástico de cálculo (MPa)."""

FTD = ACERO_B500S.ftk / GAMMA_S
"""Resistencia de cálculo a rotura (MPa)."""

EPS_YD = FYD / ACERO_B500S.es
"""Deformación de fluencia."""

EPS_UD = 0.9 * ACERO_B500S.eps_uk
"""Deformación última de cálculo."""


def test_ley_bilineal_horizontal_sigue_el_diagrama() -> None:
    """La rama horizontal llega a fyd, se mantiene hasta εud y se anula."""
    ley = ley_acero_pasivo_bilineal(ACERO_B500S, GAMMA_S)

    assert isinstance(ley, LeyElastoplastica)
    assert ley.tension(0.0) == 0.0
    assert ley.tension(0.001) == pytest.approx(200.0)
    assert ley.tension(EPS_YD) == pytest.approx(FYD)
    assert ley.tension(0.03) == pytest.approx(FYD)
    assert ley.tension(EPS_UD) == pytest.approx(FYD)
    assert ley.tension(EPS_UD + 1e-6) == 0.0


def test_ley_bilineal_horizontal_es_simetrica_y_usa_epsilon_ud() -> None:
    """La ley es simétrica a compresión y εud = 0,9·εuk."""
    ley = ley_acero_pasivo_bilineal(ACERO_B500S, GAMMA_S)

    assert ley.tension(-0.03) == pytest.approx(-FYD)
    assert ley.tension(-EPS_UD - 1e-6) == 0.0
    assert ley.deformacion_maxima_traccion == pytest.approx(EPS_UD)
    assert ley.deformacion_maxima_compresion == pytest.approx(-EPS_UD)
    assert ley.deformacion_maxima_traccion == pytest.approx(0.0675)


def test_ley_bilineal_horizontal_tangente() -> None:
    """La tangente vale Es en la rama elástica y cero en la meseta."""
    ley = ley_acero_pasivo_bilineal(ACERO_B500S, GAMMA_S)

    assert ley.modulo_tangente(0.0) == pytest.approx(200_000.0)
    assert ley.modulo_tangente(0.03) == 0.0
    assert ley.modulo_tangente(EPS_UD + 1e-6) == 0.0


def test_ley_endurecida_sigue_el_diagrama() -> None:
    """La rama inclinada pasa por (εyd, fyd) y (εud, ftd)."""
    ley = ley_acero_pasivo_endurecida(ACERO_B500S, GAMMA_S)
    deformacion_intermedia = 0.5 * (EPS_YD + EPS_UD)
    tension_intermedia = 0.5 * (FYD + FTD)

    assert isinstance(ley, LeyBilinealEndurecida)
    assert ley.deformacion_fluencia == pytest.approx(EPS_YD)
    assert ley.tension(0.0) == 0.0
    assert ley.tension(0.5 * EPS_YD) == pytest.approx(0.5 * FYD)
    assert ley.tension(EPS_YD) == pytest.approx(FYD)
    assert ley.tension(deformacion_intermedia) == pytest.approx(
        tension_intermedia
    )
    assert ley.tension(EPS_UD) == pytest.approx(FTD)
    assert ley.tension(EPS_UD + 1e-6) == 0.0


def test_ley_endurecida_es_simetrica() -> None:
    """La rama inclinada también es simétrica a compresión."""
    ley = ley_acero_pasivo_endurecida(ACERO_B500S, GAMMA_S)
    deformacion_intermedia = 0.5 * (EPS_YD + EPS_UD)
    tension_intermedia = 0.5 * (FYD + FTD)

    assert ley.tension(-deformacion_intermedia) == pytest.approx(
        -tension_intermedia
    )
    assert ley.tension(-EPS_YD) == pytest.approx(-FYD)
    assert ley.tension(-EPS_UD) == pytest.approx(-FTD)
    assert ley.deformacion_maxima_traccion == pytest.approx(EPS_UD)
    assert ley.deformacion_maxima_compresion == pytest.approx(-EPS_UD)


def test_ley_endurecida_tangente() -> None:
    """La tangente es Es en la rama elástica y la pendiente de endurecimiento."""
    ley = ley_acero_pasivo_endurecida(ACERO_B500S, GAMMA_S)
    pendiente = (FTD - FYD) / (EPS_UD - EPS_YD)
    deformacion_intermedia = 0.5 * (EPS_YD + EPS_UD)

    assert ley.modulo_tangente(0.0) == pytest.approx(200_000.0)
    assert ley.modulo_tangente(deformacion_intermedia) == pytest.approx(
        pendiente
    )
    assert ley.modulo_tangente(-deformacion_intermedia) == pytest.approx(
        pendiente
    )
    assert ley.modulo_tangente(EPS_UD + 1e-6) == 0.0


@pytest.mark.parametrize(
    "fabrica",
    [ley_acero_pasivo_bilineal, ley_acero_pasivo_endurecida],
)
def test_ley_fuera_de_alcance_sin_rama_plastica(
    fabrica: Callable[[AceroArmadura, float], LeyTensionDeformacion],
) -> None:
    """Un εuk demasiado pequeño deja εud por debajo de εyd."""
    acero_corto = AceroArmadura(
        fyk=500.0,
        ftk=550.0,
        es=200_000.0,
        eps_uk=0.002,
    )

    with pytest.raises(CasoFueraDeAlcance):
        fabrica(acero_corto, GAMMA_S)


@pytest.mark.parametrize(
    "fabrica",
    [ley_acero_pasivo_bilineal, ley_acero_pasivo_endurecida],
)
def test_ley_fuera_de_alcance_con_gamma_s_no_positivo(
    fabrica: Callable[[AceroArmadura, float], LeyTensionDeformacion],
) -> None:
    """Un coeficiente parcial no positivo no tiene sentido físico."""
    with pytest.raises(CasoFueraDeAlcance):
        fabrica(ACERO_B500S, 0.0)
