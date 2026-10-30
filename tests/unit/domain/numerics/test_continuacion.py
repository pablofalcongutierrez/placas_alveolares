"""Pruebas de los contratos de continuación y de las restricciones de arco."""

from __future__ import annotations

import inspect
import math

import numpy as np
import pytest

from placas_alveolares.domain.numerics import (
    ArcoCilindrico,
    ArcoEsferico,
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorOpcionesInvalidas,
    ErrorProblemaIncompleto,
    EstadoContinuacion,
    MotivoParada,
    OpcionesContinuacion,
    PasoContinuacion,
    ProblemaContinuacion,
    ProblemaParametrizado,
    ResultadoContinuacion,
    SolverContinuacion,
)


def test_arco_esferico_residuo_y_jacobiano() -> None:
    restriccion = ArcoEsferico(peso_parametro=0.5)
    estado_previo = EstadoContinuacion(u=(0.0, 0.0), parametro=0.0)
    u = np.array([3.0, 4.0], dtype=np.float64)
    parametro = 2.0
    radio = 5.0

    # 3² + 4² + 0,25·2² − 5² = 25 + 1 − 25 = 1
    assert restriccion.residuo(
        u,
        parametro,
        estado_previo,
        radio,
    ) == pytest.approx(1.0)

    derivada_u, derivada_parametro = restriccion.jacobiano(
        u,
        parametro,
        estado_previo,
        radio,
    )
    assert derivada_u == pytest.approx((6.0, 8.0))
    assert derivada_parametro == pytest.approx(1.0)


def test_arco_cilindrico_residuo_y_jacobiano() -> None:
    restriccion = ArcoCilindrico()
    estado_previo = EstadoContinuacion(u=(0.0, 0.0), parametro=0.0)
    u = np.array([3.0, 4.0], dtype=np.float64)
    parametro = 2.0
    radio = 5.0

    assert restriccion.residuo(
        u,
        parametro,
        estado_previo,
        radio,
    ) == pytest.approx(0.0)

    derivada_u, derivada_parametro = restriccion.jacobiano(
        u,
        parametro,
        estado_previo,
        radio,
    )
    assert derivada_u == pytest.approx((6.0, 8.0))
    assert derivada_parametro == pytest.approx(0.0)


def test_restriccion_relativa_al_estado_previo() -> None:
    restriccion = ArcoCilindrico()
    estado_previo = EstadoContinuacion(u=(1.0, 2.0), parametro=0.5)
    u = np.array([4.0, 6.0], dtype=np.float64)
    radio = 5.0

    # Δu = (3, 4); ‖Δu‖² = 25; con Δs = 5 el residuo es cero.
    assert restriccion.residuo(
        u,
        9.0,
        estado_previo,
        radio,
    ) == pytest.approx(0.0)


def test_peso_parametro_invalido() -> None:
    with pytest.raises(ErrorOpcionesInvalidas):
        ArcoEsferico(peso_parametro=0.0)

    with pytest.raises(ErrorOpcionesInvalidas):
        ArcoEsferico(peso_parametro=math.inf)


def test_radio_invalido() -> None:
    restriccion = ArcoEsferico()
    estado_previo = EstadoContinuacion(u=(0.0,), parametro=0.0)
    u = np.array([1.0], dtype=np.float64)

    with pytest.raises(ErrorOpcionesInvalidas):
        restriccion.residuo(u, 0.0, estado_previo, 0.0)


def test_estado_continuacion_validacion() -> None:
    with pytest.raises(ErrorDimensionesInvalidas):
        EstadoContinuacion(u=(), parametro=0.0)

    with pytest.raises(ErrorEvaluacionNoFinita):
        EstadoContinuacion(u=(math.nan,), parametro=0.0)

    with pytest.raises(ErrorEvaluacionNoFinita):
        EstadoContinuacion(u=(1.0,), parametro=math.nan)


def test_opciones_continuacion_validas() -> None:
    opciones = OpcionesContinuacion()

    assert opciones.radio_inicial == pytest.approx(0.1)
    assert opciones.max_pasos == 100
    assert opciones.parametro_objetivo is None


def test_opciones_continuacion_invalidas() -> None:
    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesContinuacion(radio_inicial=0.0)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesContinuacion(radio_inicial=2.0, radio_maximo=1.0)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesContinuacion(max_pasos=0)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesContinuacion(factor_crecimiento=0.5)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesContinuacion(factor_reduccion=1.0)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesContinuacion(parametro_objetivo=math.inf)


def test_problema_continuacion_agrupa_sistema_y_restriccion() -> None:
    sistema = ProblemaParametrizado(
        residuo=lambda u, parametro: np.zeros_like(u),
        jacobiano=lambda u, parametro: np.eye(u.size, dtype=np.float64),
        derivada_parametro=lambda u, parametro: np.zeros_like(u),
    )
    restriccion = ArcoEsferico()

    problema = ProblemaContinuacion(
        sistema=sistema,
        restriccion=restriccion,
    )

    assert problema.sistema is sistema
    assert problema.restriccion is restriccion


def test_problema_continuacion_requiere_derivada_parametro() -> None:
    sistema = ProblemaParametrizado(
        residuo=lambda u, parametro: np.zeros_like(u),
        jacobiano=lambda u, parametro: np.eye(u.size, dtype=np.float64),
    )

    with pytest.raises(ErrorProblemaIncompleto):
        ProblemaContinuacion(
            sistema=sistema,
            restriccion=ArcoEsferico(),
        )


def test_solver_continuacion_es_abstracto() -> None:
    assert inspect.isabstract(SolverContinuacion)
    assert "resolver" in SolverContinuacion.__abstractmethods__


def test_resultado_continuacion_inmutable() -> None:
    estado = EstadoContinuacion(u=(1.0,), parametro=0.5)
    paso = PasoContinuacion(
        indice=1,
        estado=estado,
        incremento_arco=0.1,
        iteraciones_corrector=2,
        historial_corrector=(),
        norma_residuo=1e-10,
        norma_restriccion=1e-12,
    )
    resultado = ResultadoContinuacion(
        pasos=(paso,),
        motivo_parada=MotivoParada.MAX_PASOS,
    )

    assert resultado.pasos == (paso,)
    assert resultado.motivo_parada is MotivoParada.MAX_PASOS
