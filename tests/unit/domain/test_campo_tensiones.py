"""Pruebas de la evaluación tensional por fibra."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.mechanics.campo_tensiones import evaluar_tension
from placas_alveolares.domain.mechanics.generic_laws import LeyElastica
from placas_alveolares.domain.mechanics.mallado import Triangulo
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ComponenteCalculo,
)
from placas_alveolares.domain.model.geometria import Punto
from placas_alveolares.domain.state.estado_seccion import (
    EstadoComponenteFase,
)
from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)


def _componente() -> ComponenteCalculo:
    """Componente ficticio con una malla mínima para la evaluación."""
    punto = Punto(y=0.0, z=0.0)
    return ComponenteCalculo(
        componente_id="acero",
        malla=(Triangulo(a=punto, b=punto, c=punto),),
        ley=LeyElastica(200_000.0),
    )


def test_tension_usa_el_plano_constitutivo_del_componente() -> None:
    """El pretensado impuesto se suma antes de evaluar la ley."""
    estado_componente = EstadoComponenteFase(
        componente_id="acero",
        plano_referencia=PLANO_NULO,
        deformacion_impuesta=PlanoDeformaciones(
            eps0=5.0e-3,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    plano_comun = PlanoDeformaciones(
        eps0=-1.0e-3,
        kappa_y=1.0e-6,
        kappa_z=0.0,
    )

    muestra = evaluar_tension(
        _componente(),
        estado_componente,
        plano_comun,
        Punto(y=10.0, z=20.0),
    )

    assert muestra.deformacion == pytest.approx(4.0e-3 + 2.0e-5)
    assert muestra.tension == pytest.approx(200_000.0 * 4.02e-3)
    assert muestra.plano_constitutivo.kappa_y == pytest.approx(1.0e-6)


def test_referencia_del_componente_desplaza_su_fibra_nula() -> None:
    """La fibra de tensión nula depende del plano de referencia."""
    estado_componente = EstadoComponenteFase(
        componente_id="acero",
        plano_referencia=PlanoDeformaciones(
            eps0=1.0e-3,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    plano_comun = PlanoDeformaciones(
        eps0=1.0e-3,
        kappa_y=2.0e-6,
        kappa_z=0.0,
    )

    muestra = evaluar_tension(
        _componente(),
        estado_componente,
        plano_comun,
        Punto(y=0.0, z=100.0),
    )

    assert muestra.deformacion == pytest.approx(2.0e-4)
    assert muestra.tension == pytest.approx(40.0)
