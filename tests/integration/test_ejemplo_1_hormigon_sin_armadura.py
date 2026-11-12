"""Pruebas de referencia del ejemplo 1: hormigón sin armadura."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from placas_alveolares.domain.mechanics.analisis_fases import analizar_fases
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ComponenteCalculo,
    preparar_componentes,
)
from placas_alveolares.domain.mechanics.proveedor_leyes_elasticas import (
    ProveedorLeyesElasticas,
)
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.geometria import rectangulo
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.seccion import ComponenteSeccion, Seccion
from placas_alveolares.domain.model.tiempo import Tiempo
from placas_alveolares.domain.numerics import Newton, OpcionesNewton
from placas_alveolares.domain.state.estado_seccion import EstadoSeccionFase
from placas_alveolares.norms.ce.materiales.hormigones import hormigon

_ANCHO = 400.0
_ALTO = 500.0
_AREA = _ANCHO * _ALTO
_INERCIA_Y = _ANCHO * _ALTO**3 / 12.0
_INERCIA_Z = _ALTO * _ANCHO**3 / 12.0
_MATERIAL = hormigon("HA-60")
_SOLVER = Newton(
    opciones=OpcionesNewton(
        tolerancia_residuo=1.0e-10,
        tolerancia_residuo_relativa=1.0e-10,
        max_iteraciones=100,
    )
)


@dataclass(frozen=True, slots=True)
class _CasoResuelto:
    """Estado y componente preparado para muestrear un caso."""

    estado: EstadoSeccionFase
    componente: ComponenteCalculo


def _resolver_caso(acciones: EsfuerzosInternos) -> _CasoResuelto:
    """Resuelve un caso con el pipeline completo biblioteca."""
    fase = Fase(
        indice=0,
        tiempo_inicio=Tiempo(0.0),
        tiempo_fin=Tiempo(0.0),
        acciones=acciones,
    )
    componente = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(_ANCHO, _ALTO, z_base=-_ALTO / 2.0),
        material=_MATERIAL,
    )
    modelo = ModeloEstructural(
        seccion=Seccion(componentes=(componente,)),
        fases=(fase,),
    )
    historial = analizar_fases(
        modelo,
        ProveedorLeyesElasticas(),
        _SOLVER,
    )
    estado = historial.estado(0)
    preparados = preparar_componentes(
        modelo.seccion,
        fase,
        estado,
        ProveedorLeyesElasticas(),
    )
    return _CasoResuelto(estado=estado, componente=preparados[0])


def _deformacion_y_tension(
    caso: _CasoResuelto,
    y: float,
    z: float,
) -> tuple[float, float]:
    """Devuelve deformación y tensión en un punto de la sección."""
    estado_componente = caso.estado.componente_requerido(
        caso.componente.componente_id
    )
    constitutiva = estado_componente.deformacion_constitutiva(
        caso.estado.plano_comun
    )
    deformacion = constitutiva.deformacion(y, z)
    return deformacion, caso.componente.ley.tension(deformacion)


def test_caso_1_1_flexion_my_tensiones_y_deformaciones() -> None:
    """My positivo tracciona la fibra superior y comprime la inferior."""
    momento = 100.0e6
    caso = _resolver_caso(EsfuerzosInternos(m_y=momento))
    plano = caso.estado.plano_comun

    deformacion_superior, tension_superior = _deformacion_y_tension(
        caso,
        0.0,
        _ALTO / 2.0,
    )
    deformacion_inferior, tension_inferior = _deformacion_y_tension(
        caso,
        0.0,
        -_ALTO / 2.0,
    )

    assert plano.eps0 == pytest.approx(0.0, abs=1.0e-12)
    assert plano.kappa_y == pytest.approx(
        momento / (_MATERIAL.ecm * _INERCIA_Y),
        rel=1.0e-9,
    )
    assert plano.kappa_z == pytest.approx(0.0, abs=1.0e-15)
    assert deformacion_superior == pytest.approx(
        momento * (_ALTO / 2.0) / (_MATERIAL.ecm * _INERCIA_Y),
        rel=1.0e-9,
    )
    assert deformacion_inferior == pytest.approx(-deformacion_superior)
    assert tension_superior == pytest.approx(6.0, rel=1.0e-9)
    assert tension_inferior == pytest.approx(-6.0, rel=1.0e-9)
    assert caso.estado.equilibrio is not None
    assert caso.estado.equilibrio.resultantes.m_y == pytest.approx(
        momento,
        abs=0.1,
    )


def test_caso_1_2_flexion_mz_tensiones_y_deformaciones() -> None:
    """Mz positivo comprime la fibra derecha y tracciona la izquierda."""
    momento = 50.0e6
    caso = _resolver_caso(EsfuerzosInternos(m_z=momento))
    plano = caso.estado.plano_comun

    deformacion_derecha, tension_derecha = _deformacion_y_tension(
        caso,
        _ANCHO / 2.0,
        0.0,
    )
    deformacion_izquierda, tension_izquierda = _deformacion_y_tension(
        caso,
        -_ANCHO / 2.0,
        0.0,
    )

    assert plano.eps0 == pytest.approx(0.0, abs=1.0e-12)
    assert plano.kappa_y == pytest.approx(0.0, abs=1.0e-15)
    assert plano.kappa_z == pytest.approx(
        momento / (_MATERIAL.ecm * _INERCIA_Z),
        rel=1.0e-9,
    )
    assert deformacion_derecha == pytest.approx(
        -momento * (_ANCHO / 2.0) / (_MATERIAL.ecm * _INERCIA_Z),
        rel=1.0e-9,
    )
    assert deformacion_izquierda == pytest.approx(-deformacion_derecha)
    assert tension_derecha == pytest.approx(-3.75, rel=1.0e-9)
    assert tension_izquierda == pytest.approx(3.75, rel=1.0e-9)
    assert caso.estado.equilibrio is not None
    assert caso.estado.equilibrio.resultantes.m_z == pytest.approx(
        momento,
        abs=0.1,
    )


def test_caso_1_3_compresion_con_flexion_descomprime_la_fibra_superior() -> None:
    """La compresión excéntrica deja la fibra superior en tensión nula."""
    axil = -300.0e3
    momento = 25.0e6
    caso = _resolver_caso(EsfuerzosInternos(n=axil, m_y=momento))
    plano = caso.estado.plano_comun

    deformacion_superior, tension_superior = _deformacion_y_tension(
        caso,
        0.0,
        _ALTO / 2.0,
    )
    deformacion_inferior, tension_inferior = _deformacion_y_tension(
        caso,
        0.0,
        -_ALTO / 2.0,
    )

    assert plano.eps0 == pytest.approx(
        axil / (_MATERIAL.ecm * _AREA),
        rel=1.0e-9,
    )
    assert plano.kappa_y == pytest.approx(
        momento / (_MATERIAL.ecm * _INERCIA_Y),
        rel=1.0e-9,
    )
    assert deformacion_superior == pytest.approx(0.0, abs=1.0e-12)
    assert tension_superior == pytest.approx(0.0, abs=1.0e-9)
    assert deformacion_inferior == pytest.approx(
        -2.0 * (-axil) / (_MATERIAL.ecm * _AREA),
        rel=1.0e-9,
    )
    assert tension_inferior == pytest.approx(-3.0, rel=1.0e-9)
    assert -plano.eps0 / plano.kappa_y == pytest.approx(
        _ALTO / 2.0,
        rel=1.0e-9,
    )
    assert caso.estado.equilibrio is not None
    assert caso.estado.equilibrio.resultantes.n == pytest.approx(
        axil,
        abs=0.1,
    )
    assert caso.estado.equilibrio.resultantes.m_y == pytest.approx(
        momento,
        abs=0.1,
    )
