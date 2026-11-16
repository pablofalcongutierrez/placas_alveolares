"""Pruebas de las leyes constitutivas del acero activo de la familia eurocódigo."""

from __future__ import annotations

import math
from collections.abc import Callable

import pytest

from placas_alveolares.domain.mechanics.generic_laws import LeyElastoplastica
from placas_alveolares.domain.model.materiales import AceroPretensado
from placas_alveolares.norms.ce.materiales.aceros_pretensados import (
    acero_pretensado,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance
from placas_alveolares.norms.eurocode.laws import (
    LeyBilinealEndurecida,
    ley_acero_activo_bilineal,
    ley_acero_activo_endurecida,
)

FP01K = 1_636.8
"""Límite elástico característico al 0,1 % del cordón de referencia (MPa)."""

ACERO_CON_DATOS = AceroPretensado(
    fpk=1_860.0,
    ep=195_000.0,
    fp01k=FP01K,
    eps_uk=0.035,
)
"""Cordón Y 1860 S7 con límite convencional y alargamiento explícitos."""

ACERO_SIN_DATOS = AceroPretensado(fpk=1_860.0, ep=195_000.0)
"""Cordón del que solo se conocen fpk y Ep."""

GAMMA_S = 1.15
"""Coeficiente parcial del acero."""

FP01D = FP01K / GAMMA_S
"""Límite convencional de cálculo (MPa)."""

EPS_P01D = FP01D / ACERO_CON_DATOS.ep
"""Deformación de fluencia convencional."""

FPU = ACERO_CON_DATOS.fpk / GAMMA_S
"""Resistencia última de cálculo (MPa)."""

EPS_UD = 0.9 * 0.035
"""Deformación última de cálculo."""


def test_ley_horizontal_con_datos_sigue_el_diagrama() -> None:
    """La rama horizontal llega a fp0,1d y no impone límite de deformación."""
    ley = ley_acero_activo_bilineal(ACERO_CON_DATOS, GAMMA_S)

    assert isinstance(ley, LeyElastoplastica)
    assert ley.limite_elastico == pytest.approx(FP01D)
    assert ley.tension(0.0) == 0.0
    assert ley.tension(0.001) == pytest.approx(195.0)
    assert ley.tension(EPS_P01D) == pytest.approx(FP01D)
    assert ley.tension(0.03) == pytest.approx(FP01D)
    assert ley.tension(1.0) == pytest.approx(FP01D)
    assert ley.tension(-1.0) == pytest.approx(-FP01D)
    assert ley.deformacion_ultima == math.inf
    assert ley.deformacion_maxima_traccion == math.inf
    assert ley.deformacion_maxima_compresion == -math.inf


def test_ley_horizontal_tangente() -> None:
    """La tangente vale Ep en la rama elástica y cero en la meseta."""
    ley = ley_acero_activo_bilineal(ACERO_CON_DATOS, GAMMA_S)

    assert ley.modulo_tangente(0.0) == pytest.approx(195_000.0)
    assert ley.modulo_tangente(EPS_P01D) == 0.0
    assert ley.modulo_tangente(0.03) == 0.0
    assert ley.modulo_tangente(-0.03) == 0.0


def test_ley_endurecida_con_datos_sigue_el_diagrama() -> None:
    """La rama inclinada pasa por (εp0,1d, fp0,1d) y (εud, fpk/γs)."""
    ley = ley_acero_activo_endurecida(ACERO_CON_DATOS, GAMMA_S)
    deformacion_intermedia = 0.5 * (EPS_P01D + EPS_UD)
    tension_intermedia = 0.5 * (FP01D + FPU)

    assert isinstance(ley, LeyBilinealEndurecida)
    assert ley.deformacion_fluencia == pytest.approx(EPS_P01D)
    assert ley.tension(0.0) == 0.0
    assert ley.tension(0.5 * EPS_P01D) == pytest.approx(0.5 * FP01D)
    assert ley.tension(EPS_P01D) == pytest.approx(FP01D)
    assert ley.tension(deformacion_intermedia) == pytest.approx(
        tension_intermedia
    )
    assert ley.tension(EPS_UD) == pytest.approx(FPU)
    assert ley.tension(EPS_UD + 1e-6) == 0.0
    assert ley.tension(-deformacion_intermedia) == pytest.approx(
        -tension_intermedia
    )
    assert ley.tension(-EPS_UD - 1e-6) == 0.0
    assert ley.deformacion_maxima_traccion == pytest.approx(EPS_UD)
    assert ley.deformacion_maxima_compresion == pytest.approx(-EPS_UD)


def test_ley_endurecida_tangente() -> None:
    """La tangente es Ep en la rama elástica y la pendiente de endurecimiento."""
    ley = ley_acero_activo_endurecida(ACERO_CON_DATOS, GAMMA_S)
    pendiente = (FPU - FP01D) / (EPS_UD - EPS_P01D)
    deformacion_intermedia = 0.5 * (EPS_P01D + EPS_UD)

    assert ley.modulo_tangente(0.0) == pytest.approx(195_000.0)
    assert ley.modulo_tangente(deformacion_intermedia) == pytest.approx(
        pendiente
    )
    assert ley.modulo_tangente(-deformacion_intermedia) == pytest.approx(
        pendiente
    )
    assert ley.modulo_tangente(EPS_UD + 1e-6) == 0.0


def test_ley_endurecida_sin_datos_usa_los_valores_de_recurso() -> None:
    """Sin fp0,1k ni εuk se aplican 0,9·fpk y εud = 0,02."""
    ley = ley_acero_activo_endurecida(ACERO_SIN_DATOS, GAMMA_S)
    fp01d = 0.9 * ACERO_SIN_DATOS.fpk / GAMMA_S

    assert ley.limite_elastico == pytest.approx(fp01d)
    assert ley.deformacion_ultima == pytest.approx(0.02)
    assert ley.resistencia_ultima == pytest.approx(FPU)


def test_ley_horizontal_sin_datos_usa_el_limite_de_recurso() -> None:
    """Sin fp0,1k la rama horizontal usa 0,9·fpk."""
    ley = ley_acero_activo_bilineal(ACERO_SIN_DATOS, GAMMA_S)

    assert ley.limite_elastico == pytest.approx(
        0.9 * ACERO_SIN_DATOS.fpk / GAMMA_S
    )
    assert ley.deformacion_ultima == math.inf


@pytest.mark.parametrize(
    "fabrica",
    [ley_acero_activo_bilineal, ley_acero_activo_endurecida],
)
def test_ley_activa_fuera_de_alcance_con_gamma_s_no_positivo(
    fabrica: Callable[[AceroPretensado, float], object],
) -> None:
    """Un coeficiente parcial no positivo no tiene sentido físico."""
    with pytest.raises(CasoFueraDeAlcance):
        fabrica(ACERO_CON_DATOS, 0.0)


def test_cordon_del_catalogo_usa_la_deformacion_de_recurso() -> None:
    """Los cordones del catálogo usan εud = 0,02 y fp0,1k = 0,9·fpk."""
    material = acero_pretensado("Y 1860 S7")
    ley = ley_acero_activo_endurecida(material, GAMMA_S)

    assert isinstance(ley, LeyBilinealEndurecida)
    assert ley.limite_elastico == pytest.approx(0.9 * 1_860.0 / GAMMA_S)
    assert ley.deformacion_ultima == pytest.approx(0.02)


def test_ley_endurecida_fuera_de_alcance_sin_rama_plastica() -> None:
    """Un εuk demasiado pequeño deja εud por debajo de εp0,1d."""
    acero_corto = AceroPretensado(
        fpk=1_860.0,
        ep=195_000.0,
        fp01k=1_636.8,
        eps_uk=0.001,
    )

    with pytest.raises(CasoFueraDeAlcance):
        ley_acero_activo_endurecida(acero_corto, GAMMA_S)
