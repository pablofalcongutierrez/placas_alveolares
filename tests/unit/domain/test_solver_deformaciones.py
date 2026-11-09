"""Pruebas del solver de deformaciones seccionales."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.mechanics.generic_laws import LeyElastica
from placas_alveolares.domain.mechanics.mallado import mallar
from placas_alveolares.domain.mechanics.solver_deformaciones import (
    ComponenteConLey,
    componente_con_ley,
    resultantes_seccion,
    resolver_plano_deformaciones,
)
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.geometria import rectangulo
from placas_alveolares.domain.model.materiales import Hormigon
from placas_alveolares.domain.model.seccion import ComponenteSeccion
from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)

_MODULO_HORMIGON = 30_000.0
_ANCHO = 300.0
_ALTO = 500.0
_AREA = _ANCHO * _ALTO
_INERCIA_Y = _ANCHO * _ALTO**3 / 12.0
_INERCIA_Z = _ALTO * _ANCHO**3 / 12.0


def _componente_elastico(
    *,
    ancho: float = _ANCHO,
    alto: float = _ALTO,
    y_centro: float = 0.0,
    z_base: float = -_ALTO / 2.0,
    modulo: float = _MODULO_HORMIGON,
    inicial: PlanoDeformaciones = PLANO_NULO,
) -> ComponenteConLey:
    """Componente rectangular con ley elástica."""
    geometria = rectangulo(
        ancho, alto, y_centro=y_centro, z_base=z_base
    )
    return ComponenteConLey(
        malla=mallar(geometria),
        ley=LeyElastica(modulo),
        deformacion_inicial=inicial,
    )


def test_componente_con_ley_malla_la_geometria() -> None:
    """La factoría malla la geometría y conserva el estado inicial."""
    componente = ComponenteSeccion(
        geometria=rectangulo(_ANCHO, _ALTO, z_base=-_ALTO / 2.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=_MODULO_HORMIGON),
    )

    con_ley = componente_con_ley(componente, LeyElastica(_MODULO_HORMIGON))

    assert len(con_ley.malla) > 0
    assert con_ley.deformacion_inicial == PLANO_NULO


def test_resultantes_elasticas() -> None:
    """Las resultantes reproducen N = EA·ε₀, My = −E·Iy·κy y Mz = −E·Iz·κz."""
    componente = _componente_elastico()
    plano = PlanoDeformaciones(
        eps0=1.0e-4, kappa_y=2.0e-6, kappa_z=-3.0e-6
    )

    resultantes = resultantes_seccion(plano, (componente,))

    assert resultantes.n == pytest.approx(
        _MODULO_HORMIGON * _AREA * 1.0e-4, rel=1e-9
    )
    assert resultantes.m_y == pytest.approx(
        -_MODULO_HORMIGON * _INERCIA_Y * 2.0e-6, rel=1e-9
    )
    assert resultantes.m_z == pytest.approx(
        -_MODULO_HORMIGON * _INERCIA_Z * -3.0e-6, rel=1e-9
    )


def test_resultantes_con_deformacion_inicial() -> None:
    """La deformación inicial se suma antes de evaluar la ley."""
    inicial = PlanoDeformaciones(eps0=1.0e-4, kappa_y=0.0, kappa_z=0.0)
    componente = _componente_elastico(inicial=inicial)

    resultantes = resultantes_seccion(PLANO_NULO, (componente,))

    assert resultantes.n == pytest.approx(
        _MODULO_HORMIGON * _AREA * 1.0e-4, rel=1e-9
    )
    assert resultantes.m_y == pytest.approx(0.0, abs=1e-6)
    assert resultantes.m_z == pytest.approx(0.0, abs=1e-6)


def test_axil_puro() -> None:
    """Bajo axil puro aparece solo deformación axial uniforme."""
    componente = _componente_elastico()
    acciones = EsfuerzosInternos(n=1.0e6)

    plano = resolver_plano_deformaciones(acciones, (componente,))

    assert plano.eps0 == pytest.approx(
        1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )
    assert plano.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_z == pytest.approx(0.0, abs=1e-12)


def test_flexion_pura_my() -> None:
    """Bajo My puro la curvatura y las deformaciones extremas son las elásticas."""
    componente = _componente_elastico()
    momento = 1.0e8

    plano = resolver_plano_deformaciones(
        EsfuerzosInternos(m_y=momento), (componente,)
    )

    curvatura = -momento / (_MODULO_HORMIGON * _INERCIA_Y)
    assert plano.eps0 == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_y == pytest.approx(curvatura, rel=1e-9)
    assert plano.kappa_z == pytest.approx(0.0, abs=1e-12)
    assert plano.deformacion(0.0, _ALTO / 2.0) == pytest.approx(
        curvatura * _ALTO / 2.0, rel=1e-9
    )
    assert plano.deformacion(0.0, -_ALTO / 2.0) == pytest.approx(
        -curvatura * _ALTO / 2.0, rel=1e-9
    )


def test_flexion_pura_mz() -> None:
    """Bajo Mz puro la tracción aparece en y > 0."""
    componente = _componente_elastico()
    momento = 1.0e8

    plano = resolver_plano_deformaciones(
        EsfuerzosInternos(m_z=momento), (componente,)
    )

    curvatura = -momento / (_MODULO_HORMIGON * _INERCIA_Z)
    assert plano.eps0 == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_z == pytest.approx(curvatura, rel=1e-9)
    assert plano.deformacion(_ANCHO / 2.0, 0.0) == pytest.approx(
        -curvatura * _ANCHO / 2.0, rel=1e-9
    )
    assert plano.deformacion(-_ANCHO / 2.0, 0.0) == pytest.approx(
        curvatura * _ANCHO / 2.0, rel=1e-9
    )


def test_flexion_biaxial() -> None:
    """Con leyes elásticas, axil y flexión biaxial se superponen."""
    componente = _componente_elastico()
    acciones = EsfuerzosInternos(n=1.0e6, m_y=1.0e8, m_z=1.0e8)

    plano = resolver_plano_deformaciones(acciones, (componente,))

    assert plano.eps0 == pytest.approx(
        1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )
    assert plano.kappa_y == pytest.approx(
        -1.0e8 / (_MODULO_HORMIGON * _INERCIA_Y), rel=1e-9
    )
    assert plano.kappa_z == pytest.approx(
        -1.0e8 / (_MODULO_HORMIGON * _INERCIA_Z), rel=1e-9
    )


def test_compresion() -> None:
    """Una compresión es un axil negativo y produce deformación negativa."""
    componente = _componente_elastico()

    plano = resolver_plano_deformaciones(
        EsfuerzosInternos(n=-1.0e6), (componente,)
    )

    assert plano.eps0 == pytest.approx(
        -1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )
    assert plano.eps0 < 0.0


def test_predeformacion_uniforme() -> None:
    """Sin acciones, el incremento anula la predeformación uniforme."""
    inicial = PlanoDeformaciones(eps0=5.0e-4, kappa_y=0.0, kappa_z=0.0)
    componente = _componente_elastico(inicial=inicial)

    plano = resolver_plano_deformaciones(EsfuerzosInternos(), (componente,))

    assert plano.eps0 == pytest.approx(-5.0e-4, rel=1e-9)
    assert plano.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_z == pytest.approx(0.0, abs=1e-12)


def test_predeformacion_plana() -> None:
    """Sin acciones, el incremento anula el plano inicial completo."""
    inicial = PlanoDeformaciones(
        eps0=2.0e-4, kappa_y=1.0e-6, kappa_z=-2.0e-6
    )
    componente = _componente_elastico(inicial=inicial)

    plano = resolver_plano_deformaciones(EsfuerzosInternos(), (componente,))

    assert plano.eps0 == pytest.approx(-2.0e-4, rel=1e-9)
    assert plano.kappa_y == pytest.approx(-1.0e-6, rel=1e-9)
    assert plano.kappa_z == pytest.approx(2.0e-6, rel=1e-9)


def test_transferencia_de_pretensado() -> None:
    """El cordón pretensado comprime el hormigón y equilibra la sección."""
    concreto = _componente_elastico(modulo=_MODULO_HORMIGON)
    tendon = _componente_elastico(
        ancho=50.0,
        alto=20.0,
        z_base=-10.0,
        modulo=200_000.0,
        inicial=PlanoDeformaciones(eps0=5.0e-3, kappa_y=0.0, kappa_z=0.0),
    )

    plano = resolver_plano_deformaciones(
        EsfuerzosInternos(), (concreto, tendon)
    )

    area_concreto = _AREA
    area_tendon = 50.0 * 20.0
    rigidez_concreto = _MODULO_HORMIGON * area_concreto
    rigidez_tendon = 200_000.0 * area_tendon
    incremento = -rigidez_tendon * 5.0e-3 / (
        rigidez_concreto + rigidez_tendon
    )

    assert plano.eps0 == pytest.approx(incremento, rel=1e-9)
    assert plano.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_z == pytest.approx(0.0, abs=1e-12)

    total_concreto = concreto.deformacion_inicial + plano
    total_tendon = tendon.deformacion_inicial + plano
    tension_concreto = concreto.ley.tension(
        total_concreto.deformacion(0.0, 0.0)
    )
    tension_tendon = tendon.ley.tension(
        total_tendon.deformacion(0.0, 0.0)
    )

    assert tension_concreto == pytest.approx(-6.382978723, rel=1e-9)
    assert tension_tendon == pytest.approx(957.4468085, rel=1e-9)

    resultantes = resultantes_seccion(plano, (concreto, tendon))
    assert resultantes.n == pytest.approx(0.0, abs=0.1)
    assert resultantes.m_y == pytest.approx(0.0, abs=1e-6)
    assert resultantes.m_z == pytest.approx(0.0, abs=1e-6)


def test_capa_nueva_sin_carga_queda_sin_tension() -> None:
    """Una capa nueva no se tensa si el estado previo ya está equilibrado."""
    viejo = _componente_elastico(
        inicial=PlanoDeformaciones(eps0=1.0e-4, kappa_y=0.0, kappa_z=0.0)
    )
    nuevo = _componente_elastico(ancho=_ANCHO, alto=100.0, z_base=250.0)
    fuerza_previa = _MODULO_HORMIGON * _AREA * 1.0e-4

    plano = resolver_plano_deformaciones(
        EsfuerzosInternos(n=fuerza_previa), (viejo, nuevo)
    )

    assert plano.eps0 == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_z == pytest.approx(0.0, abs=1e-12)
    tension_nueva = nuevo.ley.tension(
        (nuevo.deformacion_inicial + plano).deformacion(0.0, 300.0)
    )
    assert tension_nueva == pytest.approx(0.0, abs=1e-9)


def test_capa_nueva_aporta_rigidez_axial() -> None:
    """La capa nueva participa en la rigidez cuando se añade más carga."""
    area_nueva = 100.0 * 100.0
    viejo = _componente_elastico(
        inicial=PlanoDeformaciones(eps0=1.0e-4, kappa_y=0.0, kappa_z=0.0)
    )
    nuevo = _componente_elastico(
        ancho=100.0, alto=100.0, z_base=-50.0
    )
    fuerza_previa = _MODULO_HORMIGON * _AREA * 1.0e-4
    carga_adicional = 1.0e6

    plano = resolver_plano_deformaciones(
        EsfuerzosInternos(n=fuerza_previa + carga_adicional),
        (viejo, nuevo),
    )

    esperado = carga_adicional / (
        _MODULO_HORMIGON * (_AREA + area_nueva)
    )
    assert plano.eps0 == pytest.approx(esperado, rel=1e-9)
    assert plano.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert plano.kappa_z == pytest.approx(0.0, abs=1e-12)


def test_sin_componentes_lanza_error() -> None:
    """El solver no admite una sección vacía."""
    with pytest.raises(ErrorValidacion):
        resolver_plano_deformaciones(EsfuerzosInternos(), ())
