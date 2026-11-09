"""Resolución del plano de deformaciones que equilibra una sección.

El motor recibe las acciones internas ``(n, m_y, m_z)`` y una lista de
componentes con su ley constitutiva y su deformación inicial. Resuelve el
incremento común de deformaciones ``Δε`` tal que:

``N_int = ∫σ dA``, ``My_int = −∫σ·z dA`` y ``Mz_int = ∫σ·y dA``

igualen las acciones. La tensión de cada componente se evalúa con su
deformación total, ``ε_inicial + Δε``, de modo que el mismo motor sirve para
pretensado, fases constructivas o cualquier estado previo conocido.

Las leyes son totales: no se modela histéresis ni descarga dependiente de la
trayectoria.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.mechanics.integracion import (
    REGLA_3_PUNTOS,
    ReglaCuadratura,
)
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.mechanics.mallado import Triangulo, mallar
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.seccion import ComponenteSeccion
from placas_alveolares.domain.numerics.newton import Newton
from placas_alveolares.domain.numerics.opciones import OpcionesNewton
from placas_alveolares.domain.numerics.problema import (
    ProblemaNoLineal,
    Vector,
)
from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)
from placas_alveolares.domain.state.resultantes import ResultantesSeccion

_DEFORMACION_REFERENCIA = 1.0e-3
"""Deformación de referencia para escalar las incógnitas del solver."""

_OPCIONES_POR_DEFECTO = OpcionesNewton(
    tolerancia_residuo=1.0e-8,
    tolerancia_residuo_relativa=1.0e-8,
    max_iteraciones=50,
)
"""Opciones de convergencia usadas cuando el llamador no aporta otras."""


@dataclass(frozen=True, slots=True)
class ComponenteConLey:
    """Componente de cálculo con su ley constitutiva y su estado inicial.

    Attributes:
        malla: Triángulos del componente, precalculados una sola vez.
        ley: Ley tensión-deformación del material.
        deformacion_inicial: Plano de deformaciones que el componente ya tenía
            antes del incremento analizado. Por defecto, plano nulo.
    """

    malla: tuple[Triangulo, ...]
    ley: LeyTensionDeformacion
    deformacion_inicial: PlanoDeformaciones = PLANO_NULO


def componente_con_ley(
    componente: ComponenteSeccion,
    ley: LeyTensionDeformacion,
    deformacion_inicial: PlanoDeformaciones = PLANO_NULO,
) -> ComponenteConLey:
    """Construye un componente de cálculo mallando su geometría.

    Args:
        componente: Componente del modelo estructural.
        ley: Ley constitutiva que se asocia al componente.
        deformacion_inicial: Plano de deformaciones previo del componente.
            Por defecto, plano nulo.

    Returns:
        El componente listo para integrar tensiones, con su malla calculada.
    """
    return ComponenteConLey(
        malla=mallar(componente.geometria),
        ley=ley,
        deformacion_inicial=deformacion_inicial,
    )


def resultantes_seccion(
    incremental: PlanoDeformaciones,
    componentes: tuple[ComponenteConLey, ...],
    regla: ReglaCuadratura = REGLA_3_PUNTOS,
) -> ResultantesSeccion:
    """Integra las tensiones normales de la sección.

    Args:
        incremental: Incremento de deformaciones que se suma al estado inicial
            de cada componente.
        componentes: Componentes activos y adheridos, con su ley y su estado
            inicial.
        regla: Regla de cuadratura sobre cada triángulo. Por defecto la de tres
            puntos.

    Returns:
        Las resultantes ``(n, m_y, m_z)`` de las tensiones normales, con la
        convención de signos del proyecto.
    """
    n = 0.0
    m_y = 0.0
    m_z = 0.0
    for componente in componentes:
        total = componente.deformacion_inicial + incremental
        for triangulo in componente.malla:
            for evaluacion in regla.evaluaciones(triangulo):
                punto = evaluacion.punto
                tension = componente.ley.tension(
                    total.deformacion(punto.y, punto.z)
                )
                peso = evaluacion.peso
                n += tension * peso
                m_y -= tension * punto.z * peso
                m_z += tension * punto.y * peso
    return ResultantesSeccion(n=n, m_y=m_y, m_z=m_z)


def resolver_plano_deformaciones(
    acciones: EsfuerzosInternos,
    componentes: tuple[ComponenteConLey, ...],
    opciones: OpcionesNewton | None = None,
) -> PlanoDeformaciones:
    """Resuelve el incremento de deformaciones que equilibra las acciones.

    El incremento se normaliza antes de pasarlo a Newton: la deformación axial
    se escala con una deformación de referencia y las curvaturas con esa misma
    deformación dividida por el ancho y el alto de la sección. El residuo se
    normaliza con una fuerza y un momento de referencia deducidos de las
    acciones y del estado inicial. Esto mantiene el problema bien condicionado
    tanto con cargas grandes como con pretensado autoequilibrado.

    Args:
        acciones: Esfuerzos internos que debe equilibrar la sección. Solo se
            usan ``n``, ``m_y`` y ``m_z``; los cortantes no intervienen en el
            plano de deformaciones normales.
        componentes: Componentes activos y adheridos, con su ley y su estado
            inicial.
        opciones: Opciones de convergencia. Si es ``None`` se usan las
            opciones por defecto del módulo.

    Returns:
        El incremento común de deformaciones. El plano total de un componente
        se obtiene sumando su ``deformacion_inicial`` a este incremento.

    Raises:
        ErrorValidacion: Si no hay componentes o la sección no tiene
            dimensiones positivas.
        ErrorNoConvergencia: Si Newton no alcanza el equilibrio.
    """
    if not componentes:
        raise ErrorValidacion(
            "El cálculo de deformaciones necesita al menos un componente."
        )

    ancho, alto = _dimensiones(componentes)
    kappa_y_ref = _DEFORMACION_REFERENCIA / alto
    kappa_z_ref = _DEFORMACION_REFERENCIA / ancho

    iniciales = resultantes_seccion(PLANO_NULO, componentes)
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

    def residuo(x: Vector) -> Vector:
        plano = a_plano(x)
        resultantes = resultantes_seccion(plano, componentes)
        return np.array(
            [
                (resultantes.n - acciones.n) / fuerza_ref,
                (resultantes.m_y - acciones.m_y) / momento_ref,
                (resultantes.m_z - acciones.m_z) / momento_ref,
            ],
            dtype=np.float64,
        )

    opciones_efectivas = (
        _OPCIONES_POR_DEFECTO if opciones is None else opciones
    )
    resultado = Newton(opciones=opciones_efectivas).resolver(
        ProblemaNoLineal(residuo=residuo),
        (0.0, 0.0, 0.0),
    )
    return a_plano(np.asarray(resultado.x, dtype=np.float64))


def _dimensiones(
    componentes: tuple[ComponenteConLey, ...],
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
