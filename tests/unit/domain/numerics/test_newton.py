"""Pruebas del solver de Newton y de los problemas parametrizados."""

from __future__ import annotations

import inspect
import math
from pathlib import Path

import numpy as np
import pytest

from placas_alveolares.domain.numerics import (
    ErrorDimensionesInvalidas,
    ErrorEvaluacionNoFinita,
    ErrorJacobianoSingular,
    ErrorNoConvergencia,
    ErrorOpcionesInvalidas,
    Newton,
    OpcionesNewton,
    ProblemaNoLineal,
    ProblemaParametrizado,
    SolverNoLineal,
)


def _sistema_no_lineal(x: np.ndarray) -> np.ndarray:
    return np.array(
        [x[0] ** 2 + x[1] ** 2 - 4.0, x[0] - x[1]],
        dtype=np.float64,
    )


def _jacobiano_no_lineal(x: np.ndarray) -> np.ndarray:
    return np.array(
        [[2.0 * x[0], 2.0 * x[1]], [1.0, -1.0]],
        dtype=np.float64,
    )


def test_solver_no_lineal_es_abstracto() -> None:
    assert inspect.isabstract(SolverNoLineal)
    assert "resolver" in SolverNoLineal.__abstractmethods__


def test_sistema_lineal_escalar_converge_en_una_iteracion() -> None:
    problema = ProblemaNoLineal(
        residuo=lambda x: np.array([2.0 * x[0] - 4.0], dtype=np.float64),
        jacobiano=lambda x: np.array([[2.0]], dtype=np.float64),
    )

    resultado = Newton().resolver(problema, [0.0])

    assert resultado.x == pytest.approx((2.0,))
    assert resultado.iteraciones == 1
    assert resultado.norma_residuo == pytest.approx(0.0, abs=1e-12)
    assert resultado.norma_residuo_inicial == pytest.approx(4.0)
    assert len(resultado.historial) == 1


def test_sistema_lineal_2x2_converge_en_una_iteracion() -> None:
    matriz = np.array([[3.0, 1.0], [1.0, 2.0]], dtype=np.float64)
    termino = np.array([9.0, 8.0], dtype=np.float64)
    esperado = np.linalg.solve(matriz, termino)

    problema = ProblemaNoLineal(
        residuo=lambda x: matriz @ x - termino,
        jacobiano=lambda x: matriz,
    )

    resultado = Newton().resolver(problema, [0.0, 0.0])

    assert resultado.x == pytest.approx(tuple(esperado))
    assert resultado.iteraciones == 1
    assert resultado.norma_residuo < 1e-9


def test_sistema_no_lineal_con_jacobiano_analitico() -> None:
    problema = ProblemaNoLineal(
        _sistema_no_lineal,
        _jacobiano_no_lineal,
    )

    resultado = Newton().resolver(problema, [1.0, 1.0])

    raiz_dos = math.sqrt(2.0)
    assert resultado.x == pytest.approx((raiz_dos, raiz_dos), rel=1e-9)
    assert resultado.norma_residuo < 1e-9
    assert len(resultado.historial) == resultado.iteraciones


def test_sistema_no_lineal_con_jacobiano_numerico() -> None:
    problema = ProblemaNoLineal(_sistema_no_lineal)

    resultado = Newton().resolver(problema, [1.0, 1.0])

    raiz_dos = math.sqrt(2.0)
    assert resultado.x == pytest.approx((raiz_dos, raiz_dos), rel=1e-6)
    assert resultado.norma_residuo < 1e-6


def test_problema_parametrizado_con_parametro_fijo() -> None:
    problema = ProblemaParametrizado(
        residuo=lambda x, parametro: np.array(
            [x[0] - parametro],
            dtype=np.float64,
        ),
        jacobiano=lambda x, parametro: np.array(
            [[1.0]],
            dtype=np.float64,
        ),
        derivada_parametro=lambda x, parametro: np.array(
            [-1.0],
            dtype=np.float64,
        ),
    )

    resultado = Newton().resolver(problema.con_parametro(3.0), [0.0])

    assert resultado.x == pytest.approx((3.0,))


def test_problema_parametrizado_sin_jacobiano() -> None:
    problema = ProblemaParametrizado(
        residuo=lambda x, parametro: np.array(
            [x[0] ** 2 - parametro],
            dtype=np.float64,
        ),
    )

    resultado = Newton().resolver(problema.con_parametro(4.0), [1.0])

    assert resultado.x == pytest.approx((2.0,), rel=1e-6)


def test_jacobiano_singular() -> None:
    problema = ProblemaNoLineal(
        residuo=lambda x: np.array([x[0] ** 2 - 1.0], dtype=np.float64),
        jacobiano=lambda x: np.array([[2.0 * x[0]]], dtype=np.float64),
    )

    with pytest.raises(ErrorJacobianoSingular) as excinfo:
        Newton().resolver(problema, [0.0])

    assert excinfo.value.iteracion == 1


def test_no_convergencia_por_maximo_de_iteraciones() -> None:
    problema = ProblemaNoLineal(
        _sistema_no_lineal,
        _jacobiano_no_lineal,
    )

    with pytest.raises(ErrorNoConvergencia) as excinfo:
        Newton(OpcionesNewton(max_iteraciones=1)).resolver(
            problema,
            [1.0, 1.0],
        )

    resultado = excinfo.value.resultado
    assert resultado.iteraciones == 1
    assert len(resultado.historial) == 1
    assert resultado.historial[-1].norma_residuo == pytest.approx(
        resultado.norma_residuo
    )


def test_estancamiento_por_tolerancia_de_incremento() -> None:
    problema = ProblemaNoLineal(
        _sistema_no_lineal,
        _jacobiano_no_lineal,
    )

    with pytest.raises(ErrorNoConvergencia) as excinfo:
        Newton(
            OpcionesNewton(tolerancia_incremento=1e9),
        ).resolver(problema, [1.0, 1.0])

    assert excinfo.value.resultado.iteraciones == 1
    assert "incremento" in excinfo.value.motivo.lower()


def test_resultado_inmutable_y_historial_coherente() -> None:
    problema = ProblemaNoLineal(
        _sistema_no_lineal,
        _jacobiano_no_lineal,
    )

    resultado = Newton().resolver(problema, [1.0, 1.0])

    assert resultado.historial[-1].x == resultado.x
    assert resultado.historial[-1].numero == resultado.iteraciones
    assert resultado.historial[-1].norma_residuo == pytest.approx(
        resultado.norma_residuo
    )


def test_opciones_invalidas() -> None:
    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesNewton(max_iteraciones=0)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesNewton(tolerancia_residuo=-1.0)

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesNewton(
            tolerancia_residuo=0.0,
            tolerancia_residuo_relativa=0.0,
        )

    with pytest.raises(ErrorOpcionesInvalidas):
        OpcionesNewton(paso_diferencias_finitas=0.0)


def test_dimensiones_invalidas_del_residuo() -> None:
    problema = ProblemaNoLineal(
        residuo=lambda x: np.array([1.0, 2.0], dtype=np.float64),
        jacobiano=lambda x: np.eye(1, dtype=np.float64),
    )

    with pytest.raises(ErrorDimensionesInvalidas):
        Newton().resolver(problema, [0.0])


def test_punto_inicial_vacio() -> None:
    problema = ProblemaNoLineal(
        residuo=lambda x: np.array([], dtype=np.float64),
    )

    with pytest.raises(ErrorDimensionesInvalidas):
        Newton().resolver(problema, [])


def test_punto_inicial_no_finito() -> None:
    problema = ProblemaNoLineal(
        residuo=lambda x: np.array([0.0], dtype=np.float64),
    )

    with pytest.raises(ErrorEvaluacionNoFinita):
        Newton().resolver(problema, [math.nan])


def test_punto_inicial_que_ya_es_solucion() -> None:
    problema = ProblemaNoLineal(
        residuo=lambda x: np.array([x[0] - 2.0], dtype=np.float64),
        jacobiano=lambda x: np.array([[1.0]], dtype=np.float64),
    )

    resultado = Newton().resolver(problema, [2.0])

    assert resultado.iteraciones == 0
    assert resultado.historial == ()
    assert resultado.norma_residuo == pytest.approx(0.0)


def test_numerics_no_importa_fisica_ni_capas_exteriores() -> None:
    raiz = Path(__file__).resolve().parents[4]
    paquete = raiz / "src" / "placas_alveolares" / "domain" / "numerics"

    for archivo in paquete.rglob("*.py"):
        contenido = archivo.read_text(encoding="utf-8")
        assert "placas_alveolares.norms" not in contenido
        assert "placas_alveolares.application" not in contenido
        assert "placas_alveolares.domain.mechanics" not in contenido

