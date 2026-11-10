"""Pruebas de integración del análisis por fases y de las leyes normativas."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from placas_alveolares.domain.mechanics.analisis_fases import analizar_fases
from placas_alveolares.domain.mechanics.geometria_efectiva import (
    geometria_efectiva,
)
from placas_alveolares.domain.mechanics.generic_laws import LeyElastica
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.model.fases import (
    Fase,
    componentes_activos,
)
from placas_alveolares.domain.model.geometria import (
    Punto,
    area_geometria,
    circulo,
    rectangulo,
)
from placas_alveolares.domain.model.materiales import (
    AceroPretensado,
    Hormigon,
)
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.operaciones import (
    PerdidaPorTension,
    PretensadoPorTension,
)
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)
from placas_alveolares.domain.model.tiempo import Tiempo
from placas_alveolares.domain.numerics import Newton, OpcionesNewton
from placas_alveolares.domain.state.operaciones import (
    AdherirComponente,
    AplicarPerdidaPretensado,
    AsignarPretensado,
)
from placas_alveolares.norms.eurocode.laws import ley_hormigon_bilineal

_ANCHO = 300.0
_ALTO = 500.0
_AREA = _ANCHO * _ALTO
_MODULO_ACERO = 200_000.0
_RADIO_TENDON = 10.0


@dataclass(frozen=True, slots=True)
class _ProveedorLeyes:
    """Proveedor de leyes fijas por tipo de material."""

    ley_hormigon: LeyTensionDeformacion
    ley_acero: LeyTensionDeformacion

    def ley_para(
        self,
        componente: ComponenteSeccion,
        fase: Fase,
    ) -> LeyTensionDeformacion:
        if isinstance(componente.material, Hormigon):
            return self.ley_hormigon
        return self.ley_acero


def _modelo() -> ModeloEstructural:
    """Modelo con placa, cordón embebido y transferencia en la fase 2."""
    hormigon = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(_ANCHO, _ALTO, z_base=-_ALTO / 2.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
        fase_incorporacion=2,
    )
    tendon = ComponenteSeccion(
        id="tendon",
        geometria=circulo(
            Punto(y=0.0, z=0.0),
            radio=_RADIO_TENDON,
        ),
        material=AceroPretensado(fpk=1_860.0, ep=_MODULO_ACERO),
        fase_incorporacion=0,
        adherencia=CondicionAdherencia.ENFUNDADO,
        componente_anfitrion_id="hormigon",
    )
    seccion = Seccion(componentes=(hormigon, tendon))
    return ModeloEstructural(
        seccion=seccion,
        fases=(
            Fase(
                indice=0,
                tiempo_inicio=Tiempo(0.0),
                tiempo_fin=Tiempo(0.0),
                resolver_equilibrio=False,
                operaciones=(
                    AsignarPretensado(
                        "tendon",
                        PretensadoPorTension(1_000.0),
                    ),
                ),
            ),
            Fase(
                indice=1,
                tiempo_inicio=Tiempo(0.0),
                tiempo_fin=Tiempo(28.0),
                resolver_equilibrio=False,
                operaciones=(
                    AplicarPerdidaPretensado(
                        "tendon",
                        PerdidaPorTension(50.0),
                    ),
                ),
            ),
            Fase(
                indice=2,
                tiempo_inicio=Tiempo(28.0),
                tiempo_fin=Tiempo(28.0),
                operaciones=(AdherirComponente("tendon"),),
            ),
        ),
    )


def _solver() -> Newton:
    return Newton(
        opciones=OpcionesNewton(
            tolerancia_residuo=1.0e-8,
            tolerancia_residuo_relativa=1.0e-8,
            max_iteraciones=100,
        )
    )


def test_transferencia_con_hueco_geometrico_real() -> None:
    """El hormigón se malla descontando el cordón y no se duplica material."""
    modelo = _modelo()
    proveedor = _ProveedorLeyes(
        ley_hormigon=LeyElastica(33_000.0),
        ley_acero=LeyElastica(_MODULO_ACERO),
    )

    historial = analizar_fases(modelo, proveedor, _solver())

    assert len(historial.estados) == 3
    assert historial.estados[0].equilibrio is None
    assert historial.estados[1].equilibrio is None
    transferencia = historial.estado(2)
    assert transferencia.equilibrio is not None
    assert transferencia.equilibrio.resultantes.n == pytest.approx(0.0, abs=0.1)
    assert transferencia.equilibrio.resultantes.m_y == pytest.approx(
        0.0, abs=1e-6
    )
    assert transferencia.equilibrio.resultantes.m_z == pytest.approx(
        0.0, abs=1e-6
    )
    assert transferencia.plano_comun.eps0 < 0.0

    seccion = modelo.seccion
    activos = componentes_activos(seccion, fase=2)
    hormigon = seccion.componente_por_id("hormigon")
    tendon = seccion.componente_por_id("tendon")
    geometria_hormigon = geometria_efectiva(hormigon, activos)
    area_hormigon = area_geometria(geometria_hormigon)
    area_tendon = area_geometria(tendon.geometria)
    assert area_hormigon == pytest.approx(_AREA - area_tendon)


def test_ley_eurocode_se_inyecta_por_fase() -> None:
    """Una ley normativa puede cambiar por fase sin entrar en el dominio."""
    modelo = _modelo()
    proveedor = _ProveedorLeyes(
        ley_hormigon=ley_hormigon_bilineal(
            Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
            gamma_c=1.5,
        ),
        ley_acero=LeyElastica(_MODULO_ACERO),
    )

    historial = analizar_fases(modelo, proveedor, _solver())

    assert historial.estado(2).equilibrio is not None
    assert historial.estado(2).plano_comun.eps0 < 0.0
