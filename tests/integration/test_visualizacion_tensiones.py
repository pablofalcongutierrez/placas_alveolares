"""Pruebas de integración del contrato de visualización de tensiones."""

from __future__ import annotations

import pytest

from placas_alveolares.application.dtos.visualizacion_tensiones import (
    AdherenciaVista,
    TipoMaterialVista,
)
from placas_alveolares.application.use_cases.visualizar_tensiones import (
    construir_evolucion_alineada,
)
from placas_alveolares.domain.mechanics.analisis_fases import analizar_fases
from placas_alveolares.domain.mechanics.proveedor_leyes_elasticas import (
    ProveedorLeyesElasticas,
)
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.geometria import Punto, circulo, rectangulo
from placas_alveolares.domain.model.materiales import (
    AceroPretensado,
    Hormigon,
)
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.operaciones import PretensadoPorTension
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)
from placas_alveolares.domain.model.tiempo import Tiempo
from placas_alveolares.domain.numerics import Newton, OpcionesNewton
from placas_alveolares.domain.state.operaciones import (
    AdherirComponente,
    AsignarPretensado,
)

_ANCHO = 300.0
_ALTO = 500.0


def _modelo() -> ModeloEstructural:
    """Modelo con un cordón centrado, tesado y después adherido."""
    hormigon = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(_ANCHO, _ALTO, z_base=-_ALTO / 2.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
    )
    tendon = ComponenteSeccion(
        id="tendon",
        geometria=circulo(Punto(y=0.0, z=0.0), radio=12.0),
        material=AceroPretensado(fpk=1_860.0, ep=200_000.0),
        adherencia=CondicionAdherencia.ENFUNDADO,
        componente_anfitrion_id="hormigon",
    )
    return ModeloEstructural(
        seccion=Seccion(componentes=(hormigon, tendon)),
        fases=(
            Fase(
                indice=0,
                tiempo_inicio=Tiempo(0.0),
                tiempo_fin=Tiempo(0.0),
                resolver_equilibrio=False,
                operaciones=(
                    AsignarPretensado(
                        "tendon",
                        PretensadoPorTension(1_200.0),
                    ),
                ),
                nombre="Tesado",
            ),
            Fase(
                indice=1,
                tiempo_inicio=Tiempo(0.0),
                tiempo_fin=Tiempo(1.0),
                acciones=EsfuerzosInternos(m_y=100.0e6),
                operaciones=(AdherirComponente("tendon"),),
                nombre="Transferencia",
            ),
        ),
    )


def _solver() -> Newton:
    """Solver no lineal con tolerancias de prueba."""
    return Newton(
        OpcionesNewton(
            tolerancia_residuo=1.0e-8,
            tolerancia_residuo_relativa=1.0e-8,
            max_iteraciones=100,
        )
    )


def test_evolucion_alineada_incluye_todas_las_fases() -> None:
    """El contrato conserva fases, estados y componentes activos."""
    modelo = _modelo()
    historial = analizar_fases(
        modelo,
        ProveedorLeyesElasticas(),
        _solver(),
    )

    evolucion = construir_evolucion_alineada(
        modelo,
        historial,
        ProveedorLeyesElasticas(),
    )

    assert evolucion.version_formato == 1
    assert evolucion.unidad_longitud == "mm"
    assert evolucion.unidad_tension == "MPa"
    assert [fase.indice for fase in evolucion.fases] == [0, 1]
    assert evolucion.fases[0].nombre == "Tesado"
    assert not evolucion.fases[0].equilibrio_resuelto
    assert evolucion.fases[1].equilibrio_resuelto
    assert len(evolucion.fases[0].componentes) == 2


def test_cordon_enfundado_conserva_su_tension_sin_equilibrio() -> None:
    """La vista muestra la tensión propia aunque no contribuya al equilibrio."""
    modelo = _modelo()
    historial = analizar_fases(
        modelo,
        ProveedorLeyesElasticas(),
        _solver(),
    )

    evolucion = construir_evolucion_alineada(
        modelo,
        historial,
        ProveedorLeyesElasticas(),
    )
    fase = evolucion.fases[0]
    tendon = next(
        componente
        for componente in fase.componentes
        if componente.componente_id == "tendon"
    )
    muestras = tuple(
        muestra
        for tramo in tendon.perfil.tramos
        for muestra in tramo.muestras
    )

    assert tendon.tipo_material is TipoMaterialVista.ACERO_PRETENSADO
    assert tendon.adherencia is AdherenciaVista.ENFUNDADO
    assert muestras
    assert all(muestra.tension == pytest.approx(1_200.0) for muestra in muestras)


def test_geometria_efectiva_de_hormigon_rodea_el_cordon() -> None:
    """El perfil del hormigón se interrumpe en el hueco del cordón."""
    modelo = _modelo()
    historial = analizar_fases(
        modelo,
        ProveedorLeyesElasticas(),
        _solver(),
    )

    evolucion = construir_evolucion_alineada(
        modelo,
        historial,
        ProveedorLeyesElasticas(),
    )
    hormigon = next(
        componente
        for componente in evolucion.fases[1].componentes
        if componente.componente_id == "hormigon"
    )

    assert hormigon.tipo_material is TipoMaterialVista.HORMIGON
    assert len(hormigon.geometria.huecos) == 1
    assert len(hormigon.perfil.tramos) == 2


def test_deformacion_comun_es_coherente_en_el_sistema_girado() -> None:
    """La recta alineada cumple ε = κ·v y la línea neutra está en v = 0."""
    modelo = _modelo()
    historial = analizar_fases(
        modelo,
        ProveedorLeyesElasticas(),
        _solver(),
    )

    evolucion = construir_evolucion_alineada(
        modelo,
        historial,
        ProveedorLeyesElasticas(),
    )
    fase = evolucion.fases[1]

    assert fase.linea_neutra_definida
    for muestra in fase.deformacion_comun:
        assert muestra.deformacion == pytest.approx(
            fase.curvatura * muestra.v
        )
    assert fase.limites.vertical.minimo <= 0.0 <= fase.limites.vertical.maximo
    assert evolucion.limites_globales.vertical.minimo <= (
        fase.limites.vertical.minimo
    )
    assert evolucion.limites_globales.vertical.maximo >= (
        fase.limites.vertical.maximo
    )
