"""Pruebas de las leyes constitutivas del hormigón de la familia eurocódigo."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.model.materiales import Hormigon
from placas_alveolares.norms.errores import CasoFueraDeAlcance
from placas_alveolares.norms.eurocode.laws import (
    LeyParabolaRectangulo,
    deformaciones_tabla_3_1,
    ley_hormigon_bilineal,
    ley_hormigon_lineal,
    ley_hormigon_no_lineal,
    ley_hormigon_parabola,
)

HORMIGON_C30 = Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0)
"""Hormigón C30/37 de referencia."""


def test_tabla_3_1_para_hormigon_convencional() -> None:
    """Para fck ≤ 50 MPa las deformaciones son las de la Tabla 3.1."""
    deformaciones = deformaciones_tabla_3_1(fck=30.0, fcm=38.0)

    assert deformaciones.eps_c1 == pytest.approx(2.2e-3, abs=0.05e-3)
    assert deformaciones.eps_cu1 == pytest.approx(3.5e-3)
    assert deformaciones.eps_c2 == pytest.approx(2.0e-3)
    assert deformaciones.eps_cu2 == pytest.approx(3.5e-3)
    assert deformaciones.exponente == pytest.approx(2.0)
    assert deformaciones.eps_c3 == pytest.approx(1.75e-3)
    assert deformaciones.eps_cu3 == pytest.approx(3.5e-3)


def test_tabla_3_1_para_hormigon_de_alta_resistencia() -> None:
    """Para fck > 50 MPa se aplican las fórmulas de la Tabla 3.1."""
    deformaciones = deformaciones_tabla_3_1(fck=60.0, fcm=68.0)

    assert deformaciones.eps_c1 == pytest.approx(2.6e-3, abs=0.02e-3)
    assert deformaciones.eps_cu1 == pytest.approx(3.0e-3, abs=0.02e-3)
    assert deformaciones.eps_c2 == pytest.approx(2.3e-3, abs=0.02e-3)
    assert deformaciones.eps_cu2 == pytest.approx(2.9e-3, abs=0.02e-3)
    assert deformaciones.exponente == pytest.approx(1.6, abs=0.02)
    assert deformaciones.eps_c3 == pytest.approx(1.9e-3, abs=0.02e-3)
    assert deformaciones.eps_cu3 == pytest.approx(2.9e-3, abs=0.02e-3)


def test_tabla_3_1_en_el_limite_superior() -> None:
    """En C90/105 las fórmulas reproducen los valores tabulados."""
    deformaciones = deformaciones_tabla_3_1(fck=90.0, fcm=98.0)

    assert deformaciones.eps_c1 == pytest.approx(2.8e-3)
    assert deformaciones.eps_cu1 == pytest.approx(2.8e-3)
    assert deformaciones.eps_c2 == pytest.approx(2.6e-3, abs=0.01e-3)
    assert deformaciones.eps_cu2 == pytest.approx(2.6e-3)
    assert deformaciones.exponente == pytest.approx(1.4)
    assert deformaciones.eps_c3 == pytest.approx(2.3e-3)
    assert deformaciones.eps_cu3 == pytest.approx(2.6e-3)


@pytest.mark.parametrize("fck", [10.0, 11.9, 90.1, 100.0])
def test_tabla_3_1_fuera_de_alcance(fck: float) -> None:
    """La Tabla 3.1 solo cubre hormigones entre 12 y 90 MPa."""
    with pytest.raises(CasoFueraDeAlcance):
        deformaciones_tabla_3_1(fck=fck, fcm=fck + 8.0)


def test_parabola_rectangulo_sigue_el_diagrama() -> None:
    """La parábola alcanza fc, mantiene la meseta y se anula al agotarse."""
    ley = ley_hormigon_parabola(HORMIGON_C30, gamma_c=1.5)

    assert ley.fc == pytest.approx(20.0)
    assert ley.tension(0.0) == 0.0
    assert ley.tension(0.001) == 0.0
    assert ley.tension(-0.001) == pytest.approx(-15.0)
    assert ley.tension(-0.002) == pytest.approx(-20.0)
    assert ley.tension(-0.003) == pytest.approx(-20.0)
    assert ley.tension(-0.0035) == pytest.approx(-20.0)
    assert ley.tension(-0.0036) == 0.0


def test_parabola_rectangulo_tangente_analitica() -> None:
    """La tangente vale n·fc/εc2 en el origen, decrece y se anula en la meseta."""
    ley = ley_hormigon_parabola(HORMIGON_C30, gamma_c=1.5)

    assert ley.modulo_tangente(0.0) == pytest.approx(20_000.0)
    assert ley.modulo_tangente(-0.001) == pytest.approx(10_000.0)
    assert ley.modulo_tangente(-0.002) == pytest.approx(0.0)
    assert ley.modulo_tangente(-0.003) == pytest.approx(0.0)
    assert ley.modulo_tangente(0.001) == pytest.approx(0.0)
    assert ley.deformacion_maxima_compresion == pytest.approx(-0.0035)
    assert ley.deformacion_maxima_traccion == 0.0


def test_bilineal_sigue_el_diagrama() -> None:
    """La rama lineal llega a fc en εc3 y la meseta dura hasta εcu3."""
    ley = ley_hormigon_bilineal(HORMIGON_C30, gamma_c=1.5)

    assert ley.fc == pytest.approx(20.0)
    assert ley.tension(0.001) == 0.0
    assert ley.tension(-0.000875) == pytest.approx(-10.0)
    assert ley.tension(-0.00175) == pytest.approx(-20.0)
    assert ley.tension(-0.002) == pytest.approx(-20.0)
    assert ley.tension(-0.0035) == pytest.approx(-20.0)
    assert ley.tension(-0.0036) == 0.0


def test_bilineal_tangente_secante() -> None:
    """La pendiente de la primera rama es el módulo secante fc/εc3."""
    ley = ley_hormigon_bilineal(HORMIGON_C30, gamma_c=1.5)

    assert ley.modulo_tangente(0.0) == pytest.approx(20.0 / 0.00175)
    assert ley.modulo_tangente(-0.001) == pytest.approx(20.0 / 0.00175)
    assert ley.modulo_tangente(-0.002) == pytest.approx(0.0)
    assert ley.modulo_tangente(0.001) == pytest.approx(0.0)
    assert ley.deformacion_maxima_compresion == pytest.approx(-0.0035)
    assert ley.deformacion_maxima_traccion == 0.0


def test_general_no_lineal_alcanza_fcm_en_el_pico() -> None:
    """La tensión máxima es fcm en εc1 y su tangente se anula allí."""
    ley = ley_hormigon_no_lineal(HORMIGON_C30)

    assert ley.fc == pytest.approx(38.0)
    assert ley.tension(0.0) == 0.0
    assert ley.tension(-ley.eps_c1) == pytest.approx(-38.0)
    assert ley.modulo_tangente(0.0) == pytest.approx(1.05 * 33_000.0)
    assert ley.modulo_tangente(-ley.eps_c1) == pytest.approx(0.0, abs=1e-6)
    assert ley.deformacion_maxima_compresion == pytest.approx(-0.0035)
    assert ley.deformacion_maxima_traccion == 0.0


def test_general_no_lineal_tiene_rama_descendente() -> None:
    """Tras el pico la tensión decrece y la tangente es negativa."""
    ley = ley_hormigon_no_lineal(HORMIGON_C30)

    tension_pico = ley.tension(-ley.eps_c1)
    tension_post_pico = ley.tension(-0.003)

    assert tension_post_pico > tension_pico
    assert tension_post_pico > -ley.fc
    assert tension_post_pico < 0.0
    assert ley.modulo_tangente(-0.003) < 0.0
    assert ley.tension(-0.004) == 0.0


def test_hormigon_lineal_usa_el_modulo_secante() -> None:
    """La factoría resuelve Ecm y el módulo efectivo con fluencia."""
    ley_instantanea = ley_hormigon_lineal(HORMIGON_C30)
    ley_diferida = ley_hormigon_lineal(HORMIGON_C30, coeficiente_fluencia=2.0)

    assert ley_instantanea.tension(0.001) == pytest.approx(33.0)
    assert ley_diferida.tension(0.001) == pytest.approx(11.0)
    assert ley_instantanea.modulo_tangente(0.0) == pytest.approx(33_000.0)


def _integrales_parabola(
    ley: LeyParabolaRectangulo, n: int = 20_000
) -> tuple[float, float]:
    """Integra numéricamente |σ| y ε·|σ| sobre la zona comprimida en rotura.

    Args:
        ley: Ley parábola-rectángulo con la deformación última de compresión.
        n: Número de intervalos de integración (regla del punto medio).

    Returns:
        La resultante ``∫|σ|dε`` (MPa) y el momento ``∫ε|σ|dε`` (MPa), con
        ``ε`` como deformación de compresión positiva medida desde el eje
        neutro.
    """
    paso = ley.eps_cu2 / n
    resultante = 0.0
    momento = 0.0
    for i in range(n):
        compresion = (i + 0.5) * paso
        sigma = abs(ley.tension(-compresion))
        resultante += sigma * paso
        momento += compresion * sigma * paso
    return resultante, momento


def test_parabola_reproduce_el_bloque_rectangular() -> None:
    """La integral del diagrama en rotura aproxima el bloque rectangular.

    El bloque de cálculo usa ``η = 1,0`` y ``λ = 0,8`` para fck ≤ 50 MPa, de
    modo que su resultante es ``0,8·fc·x`` con centroide a ``0,4·x`` desde la
    fibra extrema. La parábola-rectángulo que calibra es algo más rica: su
    resultante es ``0,8095·fc·x`` y su centroide cae a ``0,416·x``.
    """
    ley = ley_hormigon_parabola(HORMIGON_C30, gamma_c=1.5)
    resultante, momento = _integrales_parabola(ley)

    factor_resultante = resultante / (ley.fc * ley.eps_cu2)
    distancia_al_extremo = 1.0 - momento / (ley.eps_cu2 * resultante)

    assert factor_resultante == pytest.approx(0.8095, rel=1e-3)
    assert distancia_al_extremo == pytest.approx(0.4160, abs=1e-3)
    assert factor_resultante == pytest.approx(0.8, rel=2e-2)
    assert distancia_al_extremo == pytest.approx(0.4, abs=2e-2)
