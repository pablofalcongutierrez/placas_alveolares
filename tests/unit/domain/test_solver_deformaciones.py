"""Pruebas del solver de deformaciones seccionales con estado global."""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.mechanics.generic_laws import (
    LeyElastica,
    LeyElastoplastica,
)
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.mechanics.mallado import mallar
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ComponenteCalculo,
)
from placas_alveolares.domain.mechanics.solver_deformaciones import (
    resolver_equilibrio_seccion,
    resultantes_seccion,
)
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.geometria import rectangulo
from placas_alveolares.domain.model.seccion import (
    CondicionAdherencia,
)
from placas_alveolares.domain.numerics import (
    Newton,
    OpcionesNewton,
    ProblemaNoLineal,
    ResultadoSolver,
    SolverNoLineal,
)
from placas_alveolares.domain.state.estado_seccion import (
    EstadoComponenteFase,
    EstadoSeccionFase,
    estado_inicial,
)
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

_SOLVER = Newton(
    opciones=OpcionesNewton(
        tolerancia_residuo=1.0e-8,
        tolerancia_residuo_relativa=1.0e-8,
        max_iteraciones=50,
    )
)
"""Newton configurado para las pruebas de equilibrio."""


class _SolverContador(SolverNoLineal):
    """Solver que delega en Newton y registra cuántas veces se invoca."""

    def __init__(self) -> None:
        self.llamadas = 0
        self.x0: Sequence[float] | None = None

    def resolver(
        self,
        problema: ProblemaNoLineal,
        x0: Sequence[float],
    ) -> ResultadoSolver:
        """Resuelve con el Newton de pruebas y registra el arranque."""
        self.llamadas += 1
        self.x0 = x0
        return _SOLVER.resolver(problema, x0)


def _componente(
    componente_id: str,
    *,
    ancho: float = _ANCHO,
    alto: float = _ALTO,
    y_centro: float = 0.0,
    z_base: float = -_ALTO / 2.0,
    ley: LeyTensionDeformacion | None = None,
    referencia: PlanoDeformaciones = PLANO_NULO,
    impuesta: PlanoDeformaciones = PLANO_NULO,
    adherencia: CondicionAdherencia = CondicionAdherencia.ADHERIDO,
) -> tuple[ComponenteCalculo, EstadoComponenteFase]:
    """Construye un componente de cálculo y su estado asociado."""
    calculo = ComponenteCalculo(
        componente_id=componente_id,
        malla=mallar(
            rectangulo(ancho, alto, y_centro=y_centro, z_base=z_base)
        ),
        ley=LeyElastica(_MODULO_HORMIGON) if ley is None else ley,
    )
    estado = EstadoComponenteFase(
        componente_id=componente_id,
        plano_referencia=referencia,
        deformacion_impuesta=impuesta,
        adherencia=adherencia,
    )
    return calculo, estado


def _estado(
    componentes: tuple[EstadoComponenteFase, ...],
    *,
    plano: PlanoDeformaciones = PLANO_NULO,
    fase: int = 0,
) -> EstadoSeccionFase:
    """Construye un estado de sección para las pruebas."""
    return EstadoSeccionFase(
        fase=fase,
        plano_comun=plano,
        componentes=componentes,
        equilibrio=None,
    )


def _componentes(
    pares: tuple[tuple[ComponenteCalculo, EstadoComponenteFase], ...],
) -> tuple[ComponenteCalculo, ...]:
    """Extrae los componentes de cálculo de una colección de pares."""
    return tuple(calculo for calculo, _ in pares)


def _estados(
    pares: tuple[tuple[ComponenteCalculo, EstadoComponenteFase], ...],
) -> tuple[EstadoComponenteFase, ...]:
    """Extrae los estados de componente de una colección de pares."""
    return tuple(estado for _, estado in pares)


def _resolver(
    acciones: EsfuerzosInternos,
    pares: tuple[tuple[ComponenteCalculo, EstadoComponenteFase], ...],
    *,
    plano: PlanoDeformaciones = PLANO_NULO,
    solver: SolverNoLineal = _SOLVER,
) -> EstadoSeccionFase:
    """Resuelve una sección preparada con el Newton de pruebas."""
    return resolver_equilibrio_seccion(
        acciones,
        _estado(_estados(pares), plano=plano),
        _componentes(pares),
        solver,
    )


def test_resultantes_elasticas() -> None:
    """Las resultantes reproducen N = EA·ε₀, My = −E·Iy·κy y Mz = −E·Iz·κz."""
    par = _componente("hormigon")
    estado = _estado(_estados((par,)))
    plano = PlanoDeformaciones(
        eps0=1.0e-4, kappa_y=2.0e-6, kappa_z=-3.0e-6
    )

    resultantes = resultantes_seccion(plano, estado, _componentes((par,)))

    assert resultantes.n == pytest.approx(
        _MODULO_HORMIGON * _AREA * 1.0e-4, rel=1e-9
    )
    assert resultantes.m_y == pytest.approx(
        -_MODULO_HORMIGON * _INERCIA_Y * 2.0e-6, rel=1e-9
    )
    assert resultantes.m_z == pytest.approx(
        -_MODULO_HORMIGON * _INERCIA_Z * -3.0e-6, rel=1e-9
    )


def test_resultantes_con_deformacion_impuesta() -> None:
    """La deformación impuesta se suma a la constitutiva."""
    impuesta = PlanoDeformaciones(eps0=1.0e-4, kappa_y=0.0, kappa_z=0.0)
    par = _componente("hormigon", impuesta=impuesta)
    estado = _estado(_estados((par,)))

    resultantes = resultantes_seccion(
        PLANO_NULO,
        estado,
        _componentes((par,)),
    )

    assert resultantes.n == pytest.approx(
        _MODULO_HORMIGON * _AREA * 1.0e-4, rel=1e-9
    )
    assert resultantes.m_y == pytest.approx(0.0, abs=1e-6)
    assert resultantes.m_z == pytest.approx(0.0, abs=1e-6)


def test_axil_puro() -> None:
    """Bajo axil puro aparece solo deformación axial uniforme."""
    par = _componente("hormigon")
    acciones = EsfuerzosInternos(n=1.0e6)

    estado = _resolver(acciones, (par,))

    assert estado.plano_comun.eps0 == pytest.approx(
        1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )
    assert estado.plano_comun.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_z == pytest.approx(0.0, abs=1e-12)
    assert estado.equilibrio is not None


def test_flexion_pura_my() -> None:
    """Bajo My puro la curvatura y las deformaciones extremas son elásticas."""
    par = _componente("hormigon")
    momento = 1.0e8

    estado = _resolver(EsfuerzosInternos(m_y=momento), (par,))

    curvatura = -momento / (_MODULO_HORMIGON * _INERCIA_Y)
    assert estado.plano_comun.eps0 == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_y == pytest.approx(curvatura, rel=1e-9)
    assert estado.plano_comun.kappa_z == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.deformacion(0.0, _ALTO / 2.0) == pytest.approx(
        curvatura * _ALTO / 2.0, rel=1e-9
    )


def test_flexion_pura_mz() -> None:
    """Bajo Mz puro la tracción aparece en y > 0."""
    par = _componente("hormigon")
    momento = 1.0e8

    estado = _resolver(EsfuerzosInternos(m_z=momento), (par,))

    curvatura = -momento / (_MODULO_HORMIGON * _INERCIA_Z)
    assert estado.plano_comun.eps0 == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_z == pytest.approx(curvatura, rel=1e-9)
    assert estado.plano_comun.deformacion(_ANCHO / 2.0, 0.0) == pytest.approx(
        -curvatura * _ANCHO / 2.0, rel=1e-9
    )


def test_flexion_biaxial() -> None:
    """Con leyes elásticas, axil y flexión biaxial se superponen."""
    par = _componente("hormigon")
    acciones = EsfuerzosInternos(n=1.0e6, m_y=1.0e8, m_z=1.0e8)

    estado = _resolver(acciones, (par,))

    assert estado.plano_comun.eps0 == pytest.approx(
        1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )
    assert estado.plano_comun.kappa_y == pytest.approx(
        -1.0e8 / (_MODULO_HORMIGON * _INERCIA_Y), rel=1e-9
    )
    assert estado.plano_comun.kappa_z == pytest.approx(
        -1.0e8 / (_MODULO_HORMIGON * _INERCIA_Z), rel=1e-9
    )


def test_compresion() -> None:
    """Una compresión es un axil negativo y produce deformación negativa."""
    par = _componente("hormigon")

    estado = _resolver(EsfuerzosInternos(n=-1.0e6), (par,))

    assert estado.plano_comun.eps0 == pytest.approx(
        -1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )
    assert estado.plano_comun.eps0 < 0.0


def test_predeformacion_uniforme() -> None:
    """Sin acciones, el plano común anula la predeformación uniforme."""
    inicial = PlanoDeformaciones(eps0=5.0e-4, kappa_y=0.0, kappa_z=0.0)
    par = _componente("hormigon", impuesta=inicial)

    estado = _resolver(EsfuerzosInternos(), (par,))

    assert estado.plano_comun.eps0 == pytest.approx(-5.0e-4, rel=1e-9)
    assert estado.plano_comun.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_z == pytest.approx(0.0, abs=1e-12)


def test_predeformacion_plana() -> None:
    """Sin acciones, el plano común anula el plano impuesto completo."""
    inicial = PlanoDeformaciones(
        eps0=2.0e-4, kappa_y=1.0e-6, kappa_z=-2.0e-6
    )
    par = _componente("hormigon", impuesta=inicial)

    estado = _resolver(EsfuerzosInternos(), (par,))

    assert estado.plano_comun.eps0 == pytest.approx(-2.0e-4, rel=1e-9)
    assert estado.plano_comun.kappa_y == pytest.approx(-1.0e-6, rel=1e-9)
    assert estado.plano_comun.kappa_z == pytest.approx(2.0e-6, rel=1e-9)


def test_transferencia_de_pretensado() -> None:
    """El cordón pretensado comprime el hormigón y equilibra la sección."""
    concreto = _componente("concreto")
    tendon = _componente(
        "tendon",
        ancho=50.0,
        alto=20.0,
        z_base=-10.0,
        ley=LeyElastica(200_000.0),
        impuesta=PlanoDeformaciones(
            eps0=5.0e-3,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    pares = (concreto, tendon)

    estado = _resolver(EsfuerzosInternos(), pares)

    area_tendon = 50.0 * 20.0
    rigidez_concreto = _MODULO_HORMIGON * _AREA
    rigidez_tendon = 200_000.0 * area_tendon
    incremento = -rigidez_tendon * 5.0e-3 / (
        rigidez_concreto + rigidez_tendon
    )

    assert estado.plano_comun.eps0 == pytest.approx(incremento, rel=1e-9)
    resultantes = resultantes_seccion(
        estado.plano_comun,
        estado,
        _componentes(pares),
    )
    assert resultantes.n == pytest.approx(0.0, abs=0.1)
    assert resultantes.m_y == pytest.approx(0.0, abs=1e-6)
    assert resultantes.m_z == pytest.approx(0.0, abs=1e-6)


def test_capa_nueva_sin_carga_queda_sin_tension() -> None:
    """Una capa nueva no se tensa si el estado previo ya está equilibrado."""
    viejo = _componente(
        "viejo",
        impuesta=PlanoDeformaciones(
            eps0=1.0e-4,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    nuevo = _componente(
        "nuevo",
        ancho=_ANCHO,
        alto=100.0,
        z_base=250.0,
    )
    fuerza_previa = _MODULO_HORMIGON * _AREA * 1.0e-4

    estado = _resolver(EsfuerzosInternos(n=fuerza_previa), (viejo, nuevo))

    assert estado.plano_comun.eps0 == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_y == pytest.approx(0.0, abs=1e-12)
    assert estado.plano_comun.kappa_z == pytest.approx(0.0, abs=1e-12)
    estado_nuevo = estado.componente_requerido("nuevo")
    tension_nueva = _componentes((nuevo,))[0].ley.tension(
        estado_nuevo.deformacion_constitutiva(
            estado.plano_comun
        ).deformacion(0.0, 300.0)
    )
    assert tension_nueva == pytest.approx(0.0, abs=1e-9)


def test_capa_nueva_aporta_rigidez_axial() -> None:
    """La capa nueva participa en la rigidez cuando se añade más carga."""
    area_nueva = 100.0 * 100.0
    viejo = _componente(
        "viejo",
        impuesta=PlanoDeformaciones(
            eps0=1.0e-4,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    nuevo = _componente(
        "nuevo",
        ancho=100.0,
        alto=100.0,
        z_base=-50.0,
    )
    fuerza_previa = _MODULO_HORMIGON * _AREA * 1.0e-4
    carga_adicional = 1.0e6

    estado = _resolver(
        EsfuerzosInternos(n=fuerza_previa + carga_adicional),
        (viejo, nuevo),
    )

    esperado = carga_adicional / (
        _MODULO_HORMIGON * (_AREA + area_nueva)
    )
    assert estado.plano_comun.eps0 == pytest.approx(esperado, rel=1e-9)


def test_ley_elastoplastica_equilibra_seccion_parcialmente_plastificada() -> None:
    """El motor converge con una ley no lineal y reproduce las acciones."""
    par = _componente(
        "hormigon",
        ley=LeyElastoplastica(
            modulo_elasticidad=_MODULO_HORMIGON,
            limite_elastico=30.0,
            deformacion_ultima=0.01,
        ),
    )
    acciones = EsfuerzosInternos(n=-3.0e6, m_y=2.0e8)

    estado = _resolver(acciones, (par,))
    resultantes = resultantes_seccion(
        estado.plano_comun,
        estado,
        _componentes((par,)),
    )

    assert resultantes.n == pytest.approx(acciones.n, abs=1.0)
    assert resultantes.m_y == pytest.approx(acciones.m_y, abs=100.0)
    assert _componentes((par,))[0].ley.tension(
        estado.plano_comun.deformacion(0.0, _ALTO / 2.0)
    ) == pytest.approx(-30.0)


def test_usa_el_solver_inyectado_y_arranca_del_plano_anterior() -> None:
    """El motor delega en el solver y usa el plano anterior como x0."""
    par = _componente("hormigon")
    plano_anterior = PlanoDeformaciones(
        eps0=1.0e-4,
        kappa_y=0.0,
        kappa_z=0.0,
    )
    solver = _SolverContador()

    estado = _resolver(
        EsfuerzosInternos(n=1.0e6),
        (par,),
        plano=plano_anterior,
        solver=solver,
    )

    assert solver.llamadas == 1
    assert solver.x0 is not None
    assert solver.x0[0] == pytest.approx(0.1)
    assert estado.plano_comun.eps0 == pytest.approx(
        1.0e6 / (_MODULO_HORMIGON * _AREA), rel=1e-9
    )


def test_componente_no_adherido_no_aporta_tensiones() -> None:
    """Un componente enfundado no participa en las resultantes comunes."""
    par = _componente(
        "tendon",
        adherencia=CondicionAdherencia.ENFUNDADO,
        impuesta=PlanoDeformaciones(
            eps0=5.0e-3,
            kappa_y=0.0,
            kappa_z=0.0,
        ),
    )
    estado = _estado(_estados((par,)))

    resultantes = resultantes_seccion(
        PLANO_NULO,
        estado,
        _componentes((par,)),
    )

    assert resultantes.n == 0.0
    assert resultantes.m_y == 0.0
    assert resultantes.m_z == 0.0


def test_sin_componentes_adheridos_lanza_error() -> None:
    """El equilibrio no admite una sección sin componentes adheridos."""
    with pytest.raises(ErrorValidacion):
        resolver_equilibrio_seccion(
            EsfuerzosInternos(),
            estado_inicial(0),
            (),
            _SOLVER,
        )
