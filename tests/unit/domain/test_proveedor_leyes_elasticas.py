"""Pruebas del proveedor de leyes elásticas lineales."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.mechanics.generic_laws import LeyElastica
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ProveedorLeyes,
)
from placas_alveolares.domain.mechanics.proveedor_leyes_elasticas import (
    ProveedorLeyesElasticas,
)
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.geometria import rectangulo
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    AceroPretensado,
    Hormigon,
    Material,
)
from placas_alveolares.domain.model.seccion import ComponenteSeccion
from placas_alveolares.domain.model.tiempo import Tiempo

_FASE = Fase(
    indice=0,
    tiempo_inicio=Tiempo(0.0),
    tiempo_fin=Tiempo(0.0),
)


@pytest.mark.parametrize(
    ("material", "modulo"),
    [
        (Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0), 33_000.0),
        (
            AceroArmadura(
                fyk=500.0,
                ftk=550.0,
                es=200_000.0,
                eps_uk=0.075,
            ),
            200_000.0,
        ),
        (AceroPretensado(fpk=1_860.0, ep=195_000.0), 195_000.0),
    ],
)
def test_ley_elastica_usa_el_modulo_del_material(
    material: Material,
    modulo: float,
) -> None:
    """Hormigón, acero pasivo y pretensado usan Ecm, Es y Ep respectivamente."""
    proveedor = ProveedorLeyesElasticas()
    componente = ComponenteSeccion(
        id="componente",
        geometria=rectangulo(100.0, 200.0),
        material=material,
    )

    ley = proveedor.ley_para(componente, _FASE)

    assert isinstance(ley, LeyElastica)
    assert ley.modulo_elasticidad == pytest.approx(modulo)
    assert ley.tension(0.001) == pytest.approx(modulo * 0.001)


def test_proveedor_elastico_cumple_el_contrato_del_dominio() -> None:
    """El proveedor es intercambiable con cualquier ProveedorLeyes."""
    proveedor: ProveedorLeyes = ProveedorLeyesElasticas()
    componente = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(100.0, 200.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
    )

    ley = proveedor.ley_para(componente, _FASE)

    assert isinstance(ley, LeyElastica)
