"""Pruebas de la geometría de la sección."""

from __future__ import annotations

import math

import pytest

from placas_alveolares.domain.model.geometria import (
    Contorno,
    GeometriaContorno,
    Punto,
    circulo,
    rectangulo,
)


def test_contorno_exige_tres_vertices() -> None:
    """Un contorno con menos de tres vértices no es válido."""
    with pytest.raises(ValueError):
        Contorno(puntos=(Punto(y=0.0, z=0.0), Punto(y=1.0, z=0.0)))


def test_rectangulo_dimensiones() -> None:
    """El rectángulo tiene cuatro vértices con las dimensiones pedidas."""
    geometria = rectangulo(ancho=300.0, alto=500.0, z_base=0.0)

    assert isinstance(geometria, GeometriaContorno)
    assert len(geometria.exterior.puntos) == 4
    assert geometria.huecos == ()

    ys = sorted({p.y for p in geometria.exterior.puntos})
    zs = sorted({p.z for p in geometria.exterior.puntos})
    assert ys == [-150.0, 150.0]
    assert zs == [0.0, 500.0]


def test_rectangulo_con_cota_de_base() -> None:
    """La cota de base desplaza verticalmente el rectángulo."""
    geometria = rectangulo(ancho=100.0, alto=200.0, z_base=-250.0)

    zs = sorted({p.z for p in geometria.exterior.puntos})
    assert zs == [-250.0, -50.0]


def test_rectangulo_desplazado_en_y() -> None:
    """El centro horizontal desplaza el rectángulo en y."""
    geometria = rectangulo(ancho=100.0, alto=200.0, y_centro=50.0)

    ys = sorted({p.y for p in geometria.exterior.puntos})
    assert ys == [0.0, 100.0]


def test_circulo_genera_poligono_inscrito() -> None:
    """Los vértices del círculo están sobre la circunferencia."""
    centro = Punto(y=10.0, z=-20.0)
    radio = 15.0
    geometria = circulo(centro, radio, n_puntos=12)

    assert len(geometria.exterior.puntos) == 12
    for punto in geometria.exterior.puntos:
        distancia = math.hypot(punto.y - centro.y, punto.z - centro.z)
        assert distancia == pytest.approx(radio)


def test_circulo_valores_por_defecto() -> None:
    """El círculo usa 16 puntos y no tiene huecos."""
    geometria = circulo(Punto(y=0.0, z=0.0), radio=5.0)

    assert len(geometria.exterior.puntos) == 16
    assert geometria.huecos == ()


def test_circulo_valida_radio_y_puntos() -> None:
    """Un radio no positivo o menos de tres puntos no son válidos."""
    with pytest.raises(ValueError):
        circulo(Punto(y=0.0, z=0.0), radio=0.0)
    with pytest.raises(ValueError):
        circulo(Punto(y=0.0, z=0.0), radio=1.0, n_puntos=2)
