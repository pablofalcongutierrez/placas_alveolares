"""Pruebas de las operaciones de estado y pretensado."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import ErrorValidacion
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
from placas_alveolares.domain.model.operaciones import (
    PerdidaPorDeformacion,
    PerdidaPorTension,
    PretensadoPorFuerza,
    PretensadoPorPlano,
    PretensadoPorTension,
)
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)
from placas_alveolares.domain.state.estado_seccion import (
    EstadoComponenteFase,
    EstadoSeccionFase,
)
from placas_alveolares.domain.state.operaciones import (
    AdherirComponente,
    AplicarPerdidaPretensado,
    AsignarDeformacionImpuesta,
    AsignarPretensado,
)
from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)

_MODULO_ACERO = 200_000.0


def _seccion() -> Seccion:
    hormigon = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(300.0, 500.0, z_base=-250.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
    )
    tendon = ComponenteSeccion(
        id="tendon",
        geometria=circulo(Punto(y=0.0, z=0.0), radio=10.0),
        material=AceroPretensado(fpk=1_860.0, ep=_MODULO_ACERO),
        adherencia=CondicionAdherencia.ENFUNDADO,
        componente_anfitrion_id="hormigon",
    )
    return Seccion(componentes=(hormigon, tendon))


def _estado(
    *,
    tendon: EstadoComponenteFase | None = None,
    plano: PlanoDeformaciones = PLANO_NULO,
) -> EstadoSeccionFase:
    estados = [
        EstadoComponenteFase(
            componente_id="hormigon",
            plano_referencia=PLANO_NULO,
        )
    ]
    if tendon is not None:
        estados.append(tendon)
    return EstadoSeccionFase(
        fase=0,
        plano_comun=plano,
        componentes=tuple(estados),
    )


def _estado_tendon(
    impuesta: PlanoDeformaciones = PLANO_NULO,
    referencia: PlanoDeformaciones = PLANO_NULO,
) -> EstadoComponenteFase:
    return EstadoComponenteFase(
        componente_id="tendon",
        plano_referencia=referencia,
        deformacion_impuesta=impuesta,
        adherencia=CondicionAdherencia.ENFUNDADO,
    )


def test_pretensado_por_fuerza_convierte_con_area_y_modulo() -> None:
    """La fuerza se convierte en deformación con el área real y Ep."""
    seccion = _seccion()
    area = area_geometria(seccion.componente_por_id("tendon").geometria)
    estado = _estado(tendon=_estado_tendon())

    actualizado = AsignarPretensado(
        "tendon",
        PretensadoPorFuerza(100_000.0),
    ).aplicar(estado, seccion)

    esperado = 100_000.0 / (area * _MODULO_ACERO)
    assert actualizado.componente_requerido(
        "tendon"
    ).deformacion_impuesta.eps0 == pytest.approx(esperado)


def test_pretensado_por_tension_y_por_plano() -> None:
    """La tensión y el plano se asignan directamente."""
    seccion = _seccion()
    estado = _estado(tendon=_estado_tendon())
    plano = PlanoDeformaciones(eps0=2.0e-3, kappa_y=1.0e-6, kappa_z=0.0)

    por_tension = AsignarPretensado(
        "tendon",
        PretensadoPorTension(1_000.0),
    ).aplicar(estado, seccion)
    por_plano = AsignarPretensado(
        "tendon",
        PretensadoPorPlano(plano),
    ).aplicar(estado, seccion)

    assert por_tension.componente_requerido(
        "tendon"
    ).deformacion_impuesta.eps0 == pytest.approx(1_000.0 / _MODULO_ACERO)
    assert (
        por_plano.componente_requerido("tendon").deformacion_impuesta == plano
    )


def test_perdida_reduce_el_pretensado_sin_invertirlo() -> None:
    """Una pérdida positiva reduce la deformación impuesta."""
    seccion = _seccion()
    inicial = PlanoDeformaciones(
        eps0=1_000.0 / _MODULO_ACERO,
        kappa_y=0.0,
        kappa_z=0.0,
    )
    estado = _estado(tendon=_estado_tendon(impuesta=inicial))

    actualizado = AplicarPerdidaPretensado(
        "tendon",
        PerdidaPorTension(50.0),
    ).aplicar(estado, seccion)
    por_deformacion = AplicarPerdidaPretensado(
        "tendon",
        PerdidaPorDeformacion(1.0e-4),
    ).aplicar(estado, seccion)

    assert actualizado.componente_requerido(
        "tendon"
    ).deformacion_impuesta.eps0 == pytest.approx(
        (1_000.0 - 50.0) / _MODULO_ACERO
    )
    assert por_deformacion.componente_requerido(
        "tendon"
    ).deformacion_impuesta.eps0 == pytest.approx(
        1_000.0 / _MODULO_ACERO - 1.0e-4
    )


def test_perdida_excesiva_lanza_error() -> None:
    """La pérdida no puede convertir el pretensado en compresión."""
    seccion = _seccion()
    estado = _estado(
        tendon=_estado_tendon(
            impuesta=PlanoDeformaciones(
                eps0=1.0e-4,
                kappa_y=0.0,
                kappa_z=0.0,
            )
        )
    )

    with pytest.raises(ErrorValidacion):
        AplicarPerdidaPretensado(
            "tendon",
            PerdidaPorDeformacion(2.0e-4),
        ).aplicar(estado, seccion)


def test_adherir_actualiza_referencia_al_plano_vigente() -> None:
    """Al adherir, la referencia pasa a ser el plano común actual."""
    seccion = _seccion()
    plano = PlanoDeformaciones(eps0=3.0e-4, kappa_y=0.0, kappa_z=0.0)
    estado = _estado(tendon=_estado_tendon(), plano=plano)

    actualizado = AdherirComponente("tendon").aplicar(estado, seccion)
    componente = actualizado.componente_requerido("tendon")

    assert componente.adherencia is CondicionAdherencia.ADHERIDO
    assert componente.plano_referencia == plano


def test_no_se_puede_adherir_dos_veces() -> None:
    """La transición de adherencia es única."""
    seccion = _seccion()
    estado = _estado(tendon=_estado_tendon())
    adherido = AdherirComponente("tendon").aplicar(estado, seccion)

    with pytest.raises(ErrorValidacion):
        AdherirComponente("tendon").aplicar(adherido, seccion)


def test_operacion_sobre_componente_inactivo_lanza_error() -> None:
    """No se puede modificar un componente que aún no está activo."""
    seccion = _seccion()
    estado = _estado()

    with pytest.raises(ErrorValidacion):
        AsignarDeformacionImpuesta(
            "tendon",
            PLANO_NULO,
        ).aplicar(estado, seccion)
