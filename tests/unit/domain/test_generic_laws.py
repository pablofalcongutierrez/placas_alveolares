"""Pruebas de las leyes constitutivas físicas genéricas."""

from __future__ import annotations

import math

import pytest

from placas_alveolares.domain.mechanics.generic_laws import (
    LeyElastica,
    LeyElastoplastica,
)


def test_ley_elastica_es_lineal_y_simetrica() -> None:
    """La ley de Hooke responde igual en tracción y compresión."""
    ley = LeyElastica(modulo_elasticidad=30_000.0)

    assert ley.tension(0.001) == pytest.approx(30.0)
    assert ley.tension(-0.001) == pytest.approx(-30.0)
    assert ley.modulo_tangente(0.002) == pytest.approx(30_000.0)
    assert ley.modulo_tangente(-0.002) == pytest.approx(30_000.0)


def test_ley_elastica_no_impone_limites() -> None:
    """La ley elástica es válida sin límite de deformación."""
    ley = LeyElastica(modulo_elasticidad=30_000.0)

    assert math.isinf(ley.deformacion_maxima_traccion)
    assert math.isinf(ley.deformacion_maxima_compresion)
    assert ley.deformacion_maxima_compresion < 0.0


def test_ley_elastoplastica_plastifica_en_el_limite_elastico() -> None:
    """Hasta la fluencia la rama es lineal; después la tensión es constante."""
    ley = LeyElastoplastica(
        modulo_elasticidad=200_000.0,
        limite_elastico=500.0,
        deformacion_ultima=0.05,
    )
    deformacion = 500.0 / 200_000.0

    assert ley.tension(deformacion / 2.0) == pytest.approx(250.0)
    assert ley.tension(deformacion * 2.0) == pytest.approx(500.0)
    assert ley.tension(-deformacion * 2.0) == pytest.approx(-500.0)
    assert ley.modulo_tangente(deformacion / 2.0) == pytest.approx(
        200_000.0
    )
    assert ley.modulo_tangente(deformacion * 2.0) == pytest.approx(0.0)


def test_ley_elastoplastica_se_agota_tras_la_deformacion_ultima() -> None:
    """Tras la deformación última el material no aporta tensión."""
    ley = LeyElastoplastica(
        modulo_elasticidad=200_000.0,
        limite_elastico=500.0,
        deformacion_ultima=0.05,
    )

    assert ley.tension(0.06) == 0.0
    assert ley.tension(-0.06) == 0.0
    assert ley.modulo_tangente(0.06) == 0.0
    assert ley.modulo_tangente(-0.06) == 0.0


def test_ley_elastoplastica_expone_sus_limites() -> None:
    """Los límites de deformación son simétricos."""
    ley = LeyElastoplastica(
        modulo_elasticidad=200_000.0,
        limite_elastico=500.0,
        deformacion_ultima=0.05,
    )

    assert ley.deformacion_maxima_traccion == pytest.approx(0.05)
    assert ley.deformacion_maxima_compresion == pytest.approx(-0.05)
