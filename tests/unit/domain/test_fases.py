"""Pruebas de las fases y las consultas de activación."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import FaseInvalida, ModeloInvalido
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
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
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)
from placas_alveolares.domain.model.tiempo import Tiempo, UnidadTiempo


def _seccion_con_fases() -> Seccion:
    placa = ComponenteSeccion(
        id="placa",
        geometria=rectangulo(300.0, 500.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
        fase_incorporacion=0,
    )
    capa = ComponenteSeccion(
        id="capa",
        geometria=rectangulo(300.0, 60.0, z_base=500.0),
        material=Hormigon(fck=25.0, fcm=33.0, ecm=31_000.0),
        fase_incorporacion=1,
    )
    cordon = ComponenteSeccion(
        id="cordon",
        geometria=circulo(Punto(y=0.0, z=100.0), radio=6.91),
        material=AceroPretensado(fpk=1_860.0, ep=195_000.0),
        fase_incorporacion=0,
        adherencia=CondicionAdherencia.ENFUNDADO,
        componente_anfitrion_id="placa",
    )
    armado = ComponenteSeccion(
        id="armado",
        geometria=circulo(Punto(y=0.0, z=50.0), radio=21.85),
        material=AceroArmadura(
            fyk=500.0,
            ftk=550.0,
            es=200_000.0,
            eps_uk=0.075,
        ),
        fase_incorporacion=0,
        componente_anfitrion_id="placa",
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
    """Una fase exige índice y tiempos, y resuelve equilibrio por defecto."""
    fase = Fase(
        indice=2,
        tiempo_inicio=Tiempo(0.0),
        tiempo_fin=Tiempo(0.0),
    )

    assert fase.indice == 2
    assert fase.nombre == ""
    assert fase.resolver_equilibrio
    assert fase.acciones.es_nulo


def test_fase_exige_indice_no_negativo() -> None:
    """El índice de una fase no puede ser negativo."""
    with pytest.raises(FaseInvalida):
        Fase(
            indice=-1,
            tiempo_inicio=Tiempo(0.0),
            tiempo_fin=Tiempo(0.0),
        )


def test_fase_sin_equilibrio_no_admite_acciones() -> None:
    """Las acciones no pueden quedar silenciosamente sin resolver."""
    with pytest.raises(FaseInvalida):
        Fase(
            indice=0,
            tiempo_inicio=Tiempo(0.0),
            tiempo_fin=Tiempo(0.0),
            acciones=EsfuerzosInternos(n=1.0),
            resolver_equilibrio=False,
        )


def test_fase_admite_intervalo_en_horas() -> None:
    """La fase puede expresar su intervalo en horas."""
    fase = Fase(
        indice=0,
        tiempo_inicio=Tiempo(0.0),
        tiempo_fin=Tiempo(12.0, UnidadTiempo.HORAS),
    )

    assert fase.tiempo_fin.dias == pytest.approx(0.5)


def test_modelo_rechaza_solape_temporal() -> None:
    """Las fases no pueden empezar antes de terminar la anterior."""
    seccion = _seccion_con_fases()
    with pytest.raises(ModeloInvalido):
        ModeloEstructural(
            seccion=seccion,
            fases=(
                Fase(
                    indice=0,
                    tiempo_inicio=Tiempo(0.0),
                    tiempo_fin=Tiempo(2.0),
                ),
                Fase(
                    indice=1,
                    tiempo_inicio=Tiempo(1.0),
                    tiempo_fin=Tiempo(3.0),
                ),
            ),
        )


def test_modelo_admite_huecos_y_fases_instantaneas() -> None:
    """Se permiten huecos temporales y fases de duración nula."""
    seccion = _seccion_con_fases()
    modelo = ModeloEstructural(
        seccion=seccion,
        fases=(
            Fase(
                indice=0,
                tiempo_inicio=Tiempo(0.0),
                tiempo_fin=Tiempo(1.0),
            ),
            Fase(
                indice=1,
                tiempo_inicio=Tiempo(2.0),
                tiempo_fin=Tiempo(2.0),
            ),
        ),
    )

    assert len(modelo.fases) == 2
