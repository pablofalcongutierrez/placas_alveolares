"""Pruebas de las fases y las consultas de activación."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import FaseInvalida
from placas_alveolares.domain.model.fases import (
    Fase,
    componentes_activos,
    componentes_adheridos,
)
from placas_alveolares.domain.model.geometria import Punto, circulo, rectangulo
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    AceroPretensado,
    Hormigon,
)
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)


def _seccion_con_fases() -> Seccion:
    placa = ComponenteSeccion(
        geometria=rectangulo(300.0, 500.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
        fase_incorporacion=0,
    )
    capa = ComponenteSeccion(
        geometria=rectangulo(300.0, 60.0, z_base=500.0),
        material=Hormigon(fck=25.0, fcm=33.0, ecm=31_000.0),
        fase_incorporacion=1,
    )
    cordon = ComponenteSeccion(
        geometria=circulo(Punto(y=0.0, z=100.0), radio=6.91),
        material=AceroPretensado(fpk=1_860.0, ep=195_000.0),
        fase_incorporacion=0,
        adherencia=CondicionAdherencia.ENFUNDADO,
    )
    armado = ComponenteSeccion(
        geometria=circulo(Punto(y=0.0, z=50.0), radio=21.85),
        material=AceroArmadura(fyk=500.0, es=200_000.0),
        fase_incorporacion=0,
    )
    return Seccion(componentes=(placa, capa, cordon, armado))


def test_componentes_activos_por_fase() -> None:
    """Solo entran los componentes incorporados hasta la fase consultada."""
    seccion = _seccion_con_fases()

    assert len(componentes_activos(seccion, fase=0)) == 3
    assert len(componentes_activos(seccion, fase=1)) == 4


def test_componentes_adheridos_excluye_enfundados() -> None:
    """Los componentes enfundados no se consideran adheridos."""
    seccion = _seccion_con_fases()
    activos = componentes_activos(seccion, fase=0)

    adheridos = componentes_adheridos(activos)

    assert len(activos) == 3
    assert len(adheridos) == 2
    assert all(c.adherencia is CondicionAdherencia.ADHERIDO for c in adheridos)


def test_fase_valores_por_defecto() -> None:
    """Una fase solo exige su índice."""
    fase = Fase(indice=2)

    assert fase.indice == 2
    assert fase.nombre == ""


def test_fase_exige_indice_no_negativo() -> None:
    """El índice de una fase no puede ser negativo."""
    with pytest.raises(FaseInvalida):
        Fase(indice=-1)
