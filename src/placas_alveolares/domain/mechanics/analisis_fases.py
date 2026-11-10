"""Orquestación del cálculo seccional a lo largo de una secuencia de fases."""

from __future__ import annotations

from dataclasses import replace

from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ProveedorLeyes,
    preparar_componentes,
)
from placas_alveolares.domain.mechanics.solver_deformaciones import (
    resolver_equilibrio_seccion,
)
from placas_alveolares.domain.errores import ModeloInvalido
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.seccion import Seccion
from placas_alveolares.domain.numerics.base import SolverNoLineal
from placas_alveolares.domain.state.estado_seccion import (
    EstadoComponenteFase,
    EstadoSeccionFase,
    estado_inicial,
)
from placas_alveolares.domain.state.historial_seccion import HistorialSeccion
from placas_alveolares.domain.state.plano_deformaciones import PLANO_NULO


def analizar_fases(
    modelo: ModeloEstructural,
    proveedor_leyes: ProveedorLeyes,
    solver: SolverNoLineal,
) -> HistorialSeccion:
    """Calcula el estado seccional de todas las fases del modelo.

    Args:
        modelo: Modelo con sección y secuencia temporal de fases.
        proveedor_leyes: Fuente de leyes constitutivas por componente y fase.
        solver: Solver no lineal inyectado.

    Returns:
        El historial completo, con un estado por fase.

    Raises:
        ErrorValidacion: Si una operación no es aplicable o no hay componentes
            adheridos cuando se solicita equilibrio.
        ErrorNoConvergencia: Si alguna fase no alcanza el equilibrio.
    """
    if not modelo.fases:
        raise ModeloInvalido("El modelo no contiene fases.")

    estado = estado_inicial(modelo.fases[0].indice)
    historial: list[EstadoSeccionFase] = []
    for fase in modelo.fases:
        estado = _activar_componentes(estado, modelo.seccion, fase)
        for operacion in fase.operaciones:
            estado = operacion.aplicar(estado, modelo.seccion)
        if fase.resolver_equilibrio:
            componentes = preparar_componentes(
                modelo.seccion,
                fase,
                estado,
                proveedor_leyes,
            )
            estado = resolver_equilibrio_seccion(
                fase.acciones,
                estado,
                componentes,
                solver,
            )
        historial.append(estado)
    return HistorialSeccion(estados=tuple(historial))


def _activar_componentes(
    estado: EstadoSeccionFase,
    seccion: Seccion,
    fase: Fase,
) -> EstadoSeccionFase:
    """Añade al estado los componentes que entran en servicio en la fase."""
    existentes = {
        componente.componente_id for componente in estado.componentes
    }
    componentes = list(estado.componentes)
    for componente in seccion.componentes:
        if (
            componente.fase_incorporacion <= fase.indice
            and componente.id not in existentes
        ):
            componentes.append(
                EstadoComponenteFase(
                    componente_id=componente.id,
                    plano_referencia=estado.plano_comun,
                    deformacion_impuesta=PLANO_NULO,
                    adherencia=componente.adherencia,
                )
            )
    return replace(
        estado,
        fase=fase.indice,
        componentes=tuple(componentes),
        equilibrio=None,
    )
