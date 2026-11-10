"""Pruebas de la geometría efectiva y de las relaciones de anfitrión."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.errores import SeccionInvalida
from placas_alveolares.domain.mechanics.geometria_efectiva import (
    geometria_efectiva,
)
from placas_alveolares.domain.model.geometria import (
    Contorno,
    GeometriaContorno,
    Punto,
    area_geometria,
    circulo,
    rectangulo,
)
from placas_alveolares.domain.model.materiales import (
    AceroPretensado,
    Hormigon,
)
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)


def _hormigon() -> Hormigon:
    return Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0)


def _acero() -> AceroPretensado:
    return AceroPretensado(fpk=1_860.0, ep=195_000.0)


def _seccion() -> Seccion:
    hormigon = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(300.0, 500.0, z_base=-250.0),
        material=_hormigon(),
    )
    tendon = ComponenteSeccion(
        id="tendon",
        geometria=circulo(Punto(y=0.0, z=0.0), radio=10.0),
        material=_acero(),
        adherencia=CondicionAdherencia.ENFUNDADO,
        componente_anfitrion_id="hormigon",
    )
    return Seccion(componentes=(hormigon, tendon))


def test_geometria_efectiva_resta_el_contorno_embebido() -> None:
    """El hormigón contiene el hueco y el acero conserva su geometría."""
    seccion = _seccion()
    hormigon = seccion.componente_por_id("hormigon")
    tendon = seccion.componente_por_id("tendon")
    activos = (hormigon, tendon)

    geometria_hormigon = geometria_efectiva(hormigon, activos)
    geometria_tendon = geometria_efectiva(tendon, activos)

    assert geometria_hormigon.huecos == (tendon.geometria.exterior,)
    assert geometria_tendon.huecos == ()
    assert area_geometria(geometria_hormigon) == pytest.approx(
        area_geometria(hormigon.geometria)
        - area_geometria(tendon.geometria)
    )


def test_componente_enfundado_tambien_genera_hueco() -> None:
    """La falta de adherencia no elimina el volumen desplazado."""
    seccion = _seccion()
    hormigon = seccion.componente_por_id("hormigon")
    tendon = seccion.componente_por_id("tendon")

    geometria = geometria_efectiva(hormigon, (hormigon, tendon))

    assert len(geometria.huecos) == 1


def test_solape_parcial_sin_anfitrion_es_invalido() -> None:
    """Dos regiones que se cruzan no pueden convivir sin relación explícita."""
    primero = ComponenteSeccion(
        id="a",
        geometria=rectangulo(300.0, 500.0, z_base=-250.0),
        material=_hormigon(),
    )
    segundo = ComponenteSeccion(
        id="b",
        geometria=rectangulo(300.0, 500.0, z_base=0.0),
        material=_hormigon(),
    )

    with pytest.raises(SeccionInvalida):
        Seccion(componentes=(primero, segundo))


def test_anfitrion_inexistente_es_invalido() -> None:
    """El identificador del anfitrión debe existir."""
    tendon = ComponenteSeccion(
        id="tendon",
        geometria=circulo(Punto(y=0.0, z=0.0), radio=10.0),
        material=_acero(),
        componente_anfitrion_id="no_existe",
    )

    with pytest.raises(SeccionInvalida):
        Seccion(componentes=(tendon,))


def test_anfitrion_debe_ser_hormigon() -> None:
    """El anfitrión declarado no puede ser otro acero."""
    primero = ComponenteSeccion(
        id="a",
        geometria=circulo(Punto(y=0.0, z=0.0), radio=10.0),
        material=_acero(),
    )
    segundo = ComponenteSeccion(
        id="b",
        geometria=circulo(Punto(y=0.0, z=0.0), radio=5.0),
        material=_acero(),
        componente_anfitrion_id="a",
    )

    with pytest.raises(SeccionInvalida):
        Seccion(componentes=(primero, segundo))


def test_acero_fuera_del_anfitrion_es_invalido() -> None:
    """El contorno embebido debe estar íntegramente dentro del anfitrión."""
    hormigon = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(300.0, 500.0, z_base=-250.0),
        material=_hormigon(),
    )
    tendon = ComponenteSeccion(
        id="tendon",
        geometria=circulo(Punto(y=0.0, z=400.0), radio=10.0),
        material=_acero(),
        componente_anfitrion_id="hormigon",
    )

    with pytest.raises(SeccionInvalida):
        Seccion(componentes=(hormigon, tendon))


def test_huecos_solapados_son_invalidos() -> None:
    """Dos huecos del mismo componente no pueden compartir área."""
    circulo_a = circulo(Punto(y=0.0, z=0.0), radio=20.0).exterior
    circulo_b = circulo(Punto(y=10.0, z=0.0), radio=20.0).exterior
    geometria = GeometriaContorno(
        exterior=Contorno(
            puntos=(
                Punto(y=-100.0, z=-100.0),
                Punto(y=100.0, z=-100.0),
                Punto(y=100.0, z=100.0),
                Punto(y=-100.0, z=100.0),
            )
        ),
        huecos=(circulo_a, circulo_b),
    )
    componente = ComponenteSeccion(
        id="hormigon",
        geometria=geometria,
        material=_hormigon(),
    )

    with pytest.raises(SeccionInvalida):
        Seccion(componentes=(componente,))
