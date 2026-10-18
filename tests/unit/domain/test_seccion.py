"""Pruebas de la sección por componentes y del modelo estructural."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import ModeloInvalido, SeccionInvalida
from placas_alveolares.domain.model.acciones import EsfuerzosInternos
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.geometria import Punto, circulo, rectangulo
from placas_alveolares.domain.model.materiales import AceroArmadura, Hormigon
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)


def _hormigon() -> Hormigon:
    return Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0)


def _componentes() -> tuple[ComponenteSeccion, ...]:
    placa = ComponenteSeccion(geometria=rectangulo(300.0, 500.0), material=_hormigon())
    armado = ComponenteSeccion(
        geometria=circulo(Punto(y=0.0, z=50.0), radio=21.85),
        material=AceroArmadura(fyk=500.0, es=200_000.0),
    )
    return (placa, armado)


def test_seccion_exige_al_menos_un_componente() -> None:
    """Una sección sin componentes no es válida."""
    with pytest.raises(SeccionInvalida):
        Seccion(componentes=())


def test_componente_exige_fase_no_negativa() -> None:
    """La fase de incorporación de un componente no puede ser negativa."""
    with pytest.raises(SeccionInvalida):
        ComponenteSeccion(
            geometria=rectangulo(300.0, 500.0),
            material=_hormigon(),
            fase_incorporacion=-1,
        )


def test_componente_valores_por_defecto() -> None:
    """Por defecto un componente entra en la fase 0 y está adherido."""
    componente = _componentes()[0]

    assert componente.fase_incorporacion == 0
    assert componente.adherencia is CondicionAdherencia.ADHERIDO


def test_modelo_fase_activa_debe_estar_definida() -> None:
    """La fase activa tiene que figurar entre las fases del modelo."""
    seccion = Seccion(componentes=_componentes())

    with pytest.raises(ModeloInvalido):
        ModeloEstructural(
            seccion=seccion,
            acciones=EsfuerzosInternos(m_y=2.0e8),
            fase_activa=1,
        )


def test_modelo_exige_fases_unicas() -> None:
    """No puede haber dos fases con el mismo índice."""
    seccion = Seccion(componentes=_componentes())

    with pytest.raises(ModeloInvalido):
        ModeloEstructural(
            seccion=seccion,
            acciones=EsfuerzosInternos(m_y=2.0e8),
            fases=(Fase(0), Fase(0)),
        )


def test_modelo_exige_fases_de_componentes_definidas() -> None:
    """Todo componente debe referenciar una fase declarada en el modelo."""
    componente = ComponenteSeccion(
        geometria=rectangulo(300.0, 500.0),
        material=_hormigon(),
        fase_incorporacion=1,
    )
    seccion = Seccion(componentes=(componente,))

    with pytest.raises(ModeloInvalido):
        ModeloEstructural(seccion=seccion, acciones=EsfuerzosInternos(m_y=2.0e8))


def test_modelo_valido() -> None:
    """Un modelo con la fase activa definida se construye sin error."""
    seccion = Seccion(componentes=_componentes())
    modelo = ModeloEstructural(
        seccion=seccion, acciones=EsfuerzosInternos(m_y=2.0e8)
    )

    assert modelo.fase_activa == 0
    assert len(modelo.fases) == 1


def test_esfuerzos_internos_biaxiales() -> None:
    """Los esfuerzos internos recogen axil y flexión en ambos ejes."""
    esfuerzos = EsfuerzosInternos(n=1.0e5, m_y=2.0e8, m_z=-1.5e8)

    assert esfuerzos.n == pytest.approx(1.0e5)
    assert esfuerzos.m_y == pytest.approx(2.0e8)
    assert esfuerzos.m_z == pytest.approx(-1.5e8)


def test_esfuerzos_internos_por_defecto() -> None:
    """Sin argumentos, todos los esfuerzos son nulos."""
    esfuerzos = EsfuerzosInternos()

    assert esfuerzos.n == 0.0
    assert esfuerzos.m_y == 0.0
    assert esfuerzos.m_z == 0.0
