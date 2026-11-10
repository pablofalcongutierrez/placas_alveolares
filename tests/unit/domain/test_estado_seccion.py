"""Pruebas del estado seccional y su historial."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import ErrorValidacion, FaseInvalida
from placas_alveolares.domain.state.estado_seccion import (
    EstadoComponenteFase,
    EstadoSeccionFase,
    estado_inicial,
)
from placas_alveolares.domain.state.historial_seccion import HistorialSeccion
from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)


def test_deformacion_constitutiva_global_menos_referencia() -> None:
    """La ley usa plano común menos referencia más deformación impuesta."""
    estado = EstadoComponenteFase(
        componente_id="cordon",
        plano_referencia=PlanoDeformaciones(
            eps0=1.0e-4,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
        deformacion_impuesta=PlanoDeformaciones(
            eps0=5.0e-3,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    comun = PlanoDeformaciones(
        eps0=2.0e-4,
        kappa_y=1.0e-6,
        kappa_z=0.0,
    )

    constitutiva = estado.deformacion_constitutiva(comun)

    assert constitutiva.eps0 == pytest.approx(5.1e-3)
    assert constitutiva.kappa_y == pytest.approx(1.0e-6)


def test_estado_inicial_esta_vacio_y_sin_equilibrio() -> None:
    """El estado anterior a la primera fase no contiene componentes."""
    estado = estado_inicial(3)

    assert estado.fase == 3
    assert estado.plano_comun == PLANO_NULO
    assert estado.componentes == ()
    assert estado.equilibrio is None


def test_estado_actualiza_y_busca_componentes() -> None:
    """El estado devuelve copias nuevas al actualizar componentes."""
    componente = EstadoComponenteFase(
        componente_id="cordon",
        plano_referencia=PLANO_NULO,
    )
    estado = EstadoSeccionFase(
        fase=0,
        plano_comun=PLANO_NULO,
        componentes=(componente,),
    )
    nuevo_plano = PlanoDeformaciones(
        eps0=1.0e-3,
        kappa_y=0.0,
        kappa_z=0.0,
    )

    actualizado = estado.con_deformacion_impuesta("cordon", nuevo_plano)

    assert estado.componente_requerido("cordon").deformacion_impuesta == PLANO_NULO
    assert (
        actualizado.componente_requerido("cordon").deformacion_impuesta
        == nuevo_plano
    )


def test_estado_rechaza_componentes_repetidos() -> None:
    """Un estado no puede contener dos veces el mismo componente."""
    componente = EstadoComponenteFase(
        componente_id="cordon",
        plano_referencia=PLANO_NULO,
    )
    with pytest.raises(ErrorValidacion):
        EstadoSeccionFase(
            fase=0,
            plano_comun=PLANO_NULO,
            componentes=(componente, componente),
        )


def test_historial_consulta_y_valida_fases() -> None:
    """El historial recupera estados y rechaza fases duplicadas."""
    estado_0 = EstadoSeccionFase(
        fase=0,
        plano_comun=PLANO_NULO,
        componentes=(),
    )
    estado_1 = EstadoSeccionFase(
        fase=1,
        plano_comun=PLANO_NULO,
        componentes=(),
    )
    historial = HistorialSeccion(estados=(estado_0, estado_1))

    assert historial.estado(1) is estado_1
    assert historial.ultimo is estado_1
    with pytest.raises(FaseInvalida):
        historial.estado(2)
    with pytest.raises(FaseInvalida):
        HistorialSeccion(estados=(estado_0, estado_0))
