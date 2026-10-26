"""Pruebas de las propiedades físicas de los materiales."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import MaterialInvalido
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    AceroPretensado,
    Hormigon,
    modulo_elastico,
)


def test_hormigon_exige_propiedades_positivas() -> None:
    """Una resistencia o módulo no positivos no son válidos."""
    with pytest.raises(MaterialInvalido):
        Hormigon(fck=0.0, fcm=38.0, ecm=33_000.0)


def test_acero_armadura_exige_propiedades_positivas() -> None:
    """Un límite elástico o módulo no positivos no son válidos."""
    with pytest.raises(MaterialInvalido):
        AceroArmadura(
            fyk=500.0,
            ftk=550.0,
            es=-200_000.0,
            eps_uk=0.075,
        )


def test_acero_armadura_exige_rotura_mayor_que_fluencia() -> None:
    """La carga de rotura no puede ser menor que el límite elástico."""
    with pytest.raises(MaterialInvalido):
        AceroArmadura(
            fyk=500.0,
            ftk=450.0,
            es=200_000.0,
            eps_uk=0.075,
        )


def test_acero_armadura_exige_alargamiento_positivo() -> None:
    """El alargamiento característico debe ser positivo."""
    with pytest.raises(MaterialInvalido):
        AceroArmadura(
            fyk=500.0,
            ftk=550.0,
            es=200_000.0,
            eps_uk=0.0,
        )


def test_acero_pretensado_exige_propiedades_positivas() -> None:
    """Una carga de rotura o módulo no positivos no son válidos."""
    with pytest.raises(MaterialInvalido):
        AceroPretensado(fpk=-1_860.0, ep=195_000.0)


def test_modulo_elastico_de_cada_material() -> None:
    """Cada material devuelve su módulo de elasticidad físico."""
    hormigon = Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0)
    armadura = AceroArmadura(
        fyk=500.0,
        ftk=550.0,
        es=200_000.0,
        eps_uk=0.075,
    )
    pretensado = AceroPretensado(fpk=1_860.0, ep=195_000.0)

    assert modulo_elastico(hormigon) == pytest.approx(33_000.0)
    assert modulo_elastico(armadura) == pytest.approx(200_000.0)
    assert modulo_elastico(pretensado) == pytest.approx(195_000.0)
