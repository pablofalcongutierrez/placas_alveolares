"""Resolución del plano de deformaciones de una sección en una fase.

El motor recibe las acciones internas ``(n, m_y, m_z)``, el estado global de
la sección y los componentes preparados con su malla y su ley. Resuelve el
plano común ``Φ = (ε₀, κ_y, κ_z)`` tal que:

``N_int = ∫σ dA``, ``My_int = −∫σ·z dA`` y ``Mz_int = ∫σ·y dA``

igualen las acciones. La deformación constitutiva de cada componente adherido
es ``Φ − Φ_referencia + deformación_impuesta``. El método numérico se inyecta
como :class:`SolverNoLineal`.
"""

from __future__ import annotations

import numpy as np

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.mechanics.integracion import (
    REGLA_3_PUNTOS,
    ReglaCuadratura,
)
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ComponenteCalculo,
)
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.seccion import CondicionAdherencia
from placas_alveolares.domain.numerics.base import SolverNoLineal
from placas_alveolares.domain.numerics.problema import (
    ProblemaNoLineal,
    Vector,
)
from placas_alveolares.domain.state.estado_seccion import (
    EstadoSeccionFase,
    ResumenEquilibrio,
)
from placas_alveolares.domain.state.plano_deformaciones import (
    PlanoDeformaciones,
)
from placas_alveolares.domain.state.resultantes import ResultantesSeccion

_DEFORMACION_REFERENCIA = 1.0e-3
"""Deformación de referencia para escalar las incógnitas del solver."""


def resultantes_seccion(
    plano_comun: PlanoDeformaciones,
    estado: EstadoSeccionFase,
    componentes: tuple[ComponenteCalculo, ...],
    regla: ReglaCuadratura = REGLA_3_PUNTOS,
) -> ResultantesSeccion:
    """Integra las tensiones normales de los componentes adheridos.

    Args:
        plano_comun: Plano cinemático de la sección.
        estado: Estado que contiene referencias y deformaciones impuestas.
        componentes: Componentes activos con malla y ley.
        regla: Regla de cuadratura sobre cada triángulo.

    Returns:
        Las resultantes ``(n, m_y, m_z)`` de las tensiones normales.
    """
    n = 0.0
    m_y = 0.0
    m_z = 0.0
    for componente in componentes:
        estado_componente = estado.componente_requerido(
            componente.componente_id
        )
        if estado_componente.adherencia is not CondicionAdherencia.ADHERIDO:
            continue
        constitutiva = estado_componente.deformacion_constitutiva(
            plano_comun
        )
        for triangulo in componente.malla:
            for evaluacion in regla.evaluaciones(triangulo):
                punto = evaluacion.punto
                tension = componente.ley.tension(
                    constitutiva.deformacion(punto.y, punto.z)
                )
                peso = evaluacion.peso
                n += tension * peso
                m_y -= tension * punto.z * peso
                m_z += tension * punto.y * peso
    return ResultantesSeccion(n=n, m_y=m_y, m_z=m_z)


def resolver_equilibrio_seccion(
    acciones: EsfuerzosInternos,
    estado: EstadoSeccionFase,
    componentes: tuple[ComponenteCalculo, ...],
    solver: SolverNoLineal,
) -> EstadoSeccionFase:
    """Resuelve el plano común que equilibra las acciones de una fase.

    Args:
        acciones: Esfuerzos internos que debe equilibrar la sección.
        estado: Estado de la fase antes del equilibrio.
        componentes: Componentes activos con malla y ley.
        solver: Solver no lineal inyectado.

    Returns:
        Un estado nuevo con el plano común y el resumen de equilibrio.

    Raises:
        ErrorValidacion: Si no hay componentes adheridos o la sección no tiene
            dimensiones positivas.
        ErrorNoConvergencia: Si el solver no alcanza el equilibrio.
    """
    adheridos = tuple(
        componente
        for componente in componentes
        if estado.componente_requerido(
            componente.componente_id
        ).adherencia
        is CondicionAdherencia.ADHERIDO
    )
    if not adheridos:
        raise ErrorValidacion(
            "El equilibrio de la sección necesita al menos un componente "
            "adherido."
        )

    ancho, alto = _dimensiones(adheridos)
    kappa_y_ref = _DEFORMACION_REFERENCIA / alto
    kappa_z_ref = _DEFORMACION_REFERENCIA / ancho

    iniciales = resultantes_seccion(
        estado.plano_comun,
        estado,
        componentes,
    )
    fuerza_ref = max(abs(iniciales.n), abs(acciones.n), 1.0)
    momento_ref = max(
        abs(iniciales.m_y),
        abs(iniciales.m_z),
        abs(acciones.m_y),
        abs(acciones.m_z),
        1.0,
    )

    def a_plano(x: Vector) -> PlanoDeformaciones:
        return PlanoDeformaciones(
            eps0=float(x[0]) * _DEFORMACION_REFERENCIA,
            kappa_y=float(x[1]) * kappa_y_ref,
            kappa_z=float(x[2]) * kappa_z_ref,
        )

    def a_vector(plano: PlanoDeformaciones) -> tuple[float, float, float]:
        return (
            plano.eps0 / _DEFORMACION_REFERENCIA,
            plano.kappa_y / kappa_y_ref,
            plano.kappa_z / kappa_z_ref,
        )

    def residuo(x: Vector) -> Vector:
        plano = a_plano(x)
        resultantes = resultantes_seccion(plano, estado, componentes)
        return np.array(
            [
                (resultantes.n - acciones.n) / fuerza_ref,
                (resultantes.m_y - acciones.m_y) / momento_ref,
                (resultantes.m_z - acciones.m_z) / momento_ref,
            ],
            dtype=np.float64,
        )

    resultado = solver.resolver(
        ProblemaNoLineal(residuo=residuo),
        a_vector(estado.plano_comun),
    )
    plano = a_plano(np.asarray(resultado.x, dtype=np.float64))
    resultantes = resultantes_seccion(plano, estado, componentes)
    resumen = ResumenEquilibrio(
        resultantes=resultantes,
        iteraciones=resultado.iteraciones,
        norma_residuo=resultado.norma_residuo,
        norma_residuo_inicial=resultado.norma_residuo_inicial,
    )
    return estado.con_plano_y_resumen(plano, resumen)


def _dimensiones(
    componentes: tuple[ComponenteCalculo, ...],
) -> tuple[float, float]:
    """Ancho y alto del contorno envolvente de los componentes.

    Args:
        componentes: Componentes con su malla ya calculada.

    Returns:
        El ancho (dirección ``y``) y el alto (dirección ``z``) en mm.

    Raises:
        ErrorValidacion: Si no hay puntos o alguna dimensión no es positiva.
    """
    puntos = [
        punto
        for componente in componentes
        for triangulo in componente.malla
        for punto in (triangulo.a, triangulo.b, triangulo.c)
    ]
    if not puntos:
        raise ErrorValidacion(
            "Los componentes no contienen puntos para calcular dimensiones."
        )

    ancho = max(punto.y for punto in puntos) - min(
        punto.y for punto in puntos
    )
    alto = max(punto.z for punto in puntos) - min(
        punto.z for punto in puntos
    )
    if ancho <= 0.0 or alto <= 0.0:
        raise ErrorValidacion(
            "La sección debe tener ancho y alto estrictamente positivos."
        )
    return ancho, alto
