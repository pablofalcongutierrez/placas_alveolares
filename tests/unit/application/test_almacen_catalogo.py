"""Pruebas del catálogo genérico en memoria."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from placas_alveolares.application.almacen_catalogo import AlmacenCatalogo
from placas_alveolares.application.errores import (
    EntradaCatalogoInvalida,
    EntradaDuplicada,
    EntradaProtegida,
)
from placas_alveolares.application.ports.catalogo import Catalogo
from placas_alveolares.application.ports.entradas_catalogo import (
    EntradaCatalogo,
    OrigenEntrada,
)
from placas_alveolares.domain.checking.kinds import NormId


@dataclass(frozen=True, slots=True)
class DatoPrueba:
    """Dato arbitrario para comprobar que el catálogo no depende del dominio."""

    valor: int


def _entrada_normativa(
    nombre: str,
    norma: NormId,
    valor: int,
    *,
    referencia: str,
) -> EntradaCatalogo[DatoPrueba]:
    """Construye un preset normativo de prueba."""
    return EntradaCatalogo(
        nombre=nombre,
        origen=OrigenEntrada.NORMATIVO,
        valor=DatoPrueba(valor),
        norma=norma,
        edicion="edición de prueba",
        referencia=referencia,
    )


def _almacen() -> Catalogo[DatoPrueba]:
    """Catálogo con dos normas y un nombre repetido entre ambas."""
    return AlmacenCatalogo(
        (
            _entrada_normativa(
                "B 500 S", NormId.CE, 500, referencia="tabla 34.2.a"
            ),
            _entrada_normativa(
                "B 500 S", NormId.EC2, 510, referencia="3.2.7"
            ),
            _entrada_normativa(
                "HA-30", NormId.CE, 30, referencia="tabla 3.1"
            ),
        )
    )


def test_lista_presets_con_norma_y_procedencia() -> None:
    """Los presets se listan con su norma, origen y referencia."""
    entradas = _almacen().listar()

    assert [entrada.nombre for entrada in entradas] == [
        "B 500 S",
        "B 500 S",
        "HA-30",
    ]
    assert [entrada.norma for entrada in entradas] == [
        NormId.CE,
        NormId.EC2,
        NormId.CE,
    ]
    assert all(
        entrada.origen is OrigenEntrada.NORMATIVO for entrada in entradas
    )
    assert entradas[0].edicion == "edición de prueba"
    assert entradas[0].referencia == "tabla 34.2.a"


def test_obtiene_el_mismo_nombre_en_normas_distintas() -> None:
    """La norma forma parte de la identidad de un preset."""
    catalogo = _almacen()

    assert catalogo.obtener("B 500 S", norma=NormId.CE) == DatoPrueba(500)
    assert catalogo.obtener("B 500 S", norma=NormId.EC2) == DatoPrueba(510)


def test_obtener_inexistente_devuelve_none() -> None:
    """Un nombre o una combinación de norma y nombre desconocidos dan None."""
    catalogo = _almacen()

    assert catalogo.obtener("B 600 S", norma=NormId.CE) is None
    assert catalogo.obtener("B 500 S") is None


def test_registra_y_obtiene_usuario_independiente_de_la_norma() -> None:
    """Una entrada de usuario no pertenece a ninguna norma."""
    catalogo = _almacen()

    catalogo.registrar("Mi dato", DatoPrueba(42))

    assert catalogo.obtener("Mi dato") == DatoPrueba(42)
    entrada = catalogo.listar()[-1]
    assert entrada.origen is OrigenEntrada.USUARIO
    assert entrada.norma is None
    assert entrada.edicion is None
    assert entrada.referencia is None


def test_registrar_sustituye_una_entrada_de_usuario() -> None:
    """Registrar de nuevo el mismo nombre actualiza su valor."""
    catalogo = _almacen()

    catalogo.registrar("Mi dato", DatoPrueba(42))
    catalogo.registrar("Mi dato", DatoPrueba(43))

    assert catalogo.obtener("Mi dato") == DatoPrueba(43)
    usuarios = [
        entrada
        for entrada in catalogo.listar()
        if entrada.origen is OrigenEntrada.USUARIO
    ]
    assert len(usuarios) == 1


def test_elimina_una_entrada_de_usuario() -> None:
    """Eliminar un dato de usuario lo retira sin afectar a los presets."""
    catalogo = _almacen()
    catalogo.registrar("Mi dato", DatoPrueba(42))

    catalogo.eliminar("Mi dato")

    assert catalogo.obtener("Mi dato") is None
    assert catalogo.obtener("B 500 S", norma=NormId.CE) == DatoPrueba(500)


def test_lista_disponibles_incluye_presets_de_la_norma_y_usuarios() -> None:
    """Lo disponible para una norma son sus presets y los datos de usuario."""
    catalogo = _almacen()
    catalogo.registrar("Mi dato", DatoPrueba(42))

    disponibles = catalogo.listar_disponibles(NormId.CE)

    assert [entrada.nombre for entrada in disponibles] == [
        "B 500 S",
        "HA-30",
        "Mi dato",
    ]
    assert [entrada.norma for entrada in disponibles] == [
        NormId.CE,
        NormId.CE,
        None,
    ]


def test_protege_los_presets_normativos() -> None:
    """Registrar o eliminar un nombre normativo lanza EntradaProtegida."""
    catalogo = _almacen()

    with pytest.raises(EntradaProtegida):
        catalogo.registrar("B 500 S", DatoPrueba(999))
    with pytest.raises(EntradaProtegida):
        catalogo.eliminar("B 500 S")

    assert catalogo.obtener("B 500 S", norma=NormId.CE) == DatoPrueba(500)
    assert catalogo.obtener("B 500 S", norma=NormId.EC2) == DatoPrueba(510)


def test_rechaza_presets_duplicados_de_la_misma_norma() -> None:
    """Dos presets con la misma norma y nombre no pueden coexistir."""
    entrada = _entrada_normativa(
        "B 500 S", NormId.CE, 500, referencia="tabla 34.2.a"
    )

    with pytest.raises(EntradaDuplicada):
        AlmacenCatalogo((entrada, entrada))


def test_entrada_normativa_exige_norma() -> None:
    """Un preset sin norma no representa una entrada válida."""
    with pytest.raises(EntradaCatalogoInvalida):
        EntradaCatalogo(
            nombre="B 500 S",
            origen=OrigenEntrada.NORMATIVO,
            valor=DatoPrueba(500),
        )


def test_entrada_de_usuario_no_admite_metadatos_normativos() -> None:
    """Una entrada de usuario no puede declarar una norma."""
    with pytest.raises(EntradaCatalogoInvalida):
        EntradaCatalogo(
            nombre="Mi dato",
            origen=OrigenEntrada.USUARIO,
            valor=DatoPrueba(42),
            norma=NormId.CE,
        )


def test_almacen_solo_acepta_presets_normativos() -> None:
    """El constructor rechaza una entrada de usuario como preset."""
    entrada_usuario = EntradaCatalogo(
        nombre="Mi dato",
        origen=OrigenEntrada.USUARIO,
        valor=DatoPrueba(42),
    )

    with pytest.raises(EntradaCatalogoInvalida):
        AlmacenCatalogo((entrada_usuario,))


def test_rechaza_nombres_vacios() -> None:
    """Una entrada con nombre vacío no es válida."""
    with pytest.raises(EntradaCatalogoInvalida):
        EntradaCatalogo(
            nombre="   ",
            origen=OrigenEntrada.USUARIO,
            valor=DatoPrueba(42),
        )
