"""Entradas de los catálogos de aplicación y su procedencia.

Una entrada puede ser **normativa** (preset inmutable inyectado desde
``norms`` en la composición) o de **usuario** (dato editable de la biblioteca).
La distinción permite a la UI señalarlas y protege las normativas de borrado o
modificación.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from placas_alveolares.application.errores import EntradaCatalogoInvalida
from placas_alveolares.domain.checking.kinds import NormId


class OrigenEntrada(StrEnum):
    """Procedencia de una entrada del catálogo."""

    NORMATIVO = "normativo"
    USUARIO = "usuario"


@dataclass(frozen=True, slots=True)
class EntradaCatalogo[T]:
    """Entrada de un catálogo con su valor y procedencia.

    Se espera que ``T`` sea inmutable, siguiendo la convención de dataclasses
    ``frozen`` y ``slots`` del proyecto, para preservar la invarianza de los
    presets normativos.

    Attributes:
        nombre: Clave visible de la entrada.
        origen: Indica si es un preset normativo o un dato de usuario.
        valor: Dato almacenado.
        norma: Norma de la que procede un preset; ``None`` para el usuario.
        edicion: Edición o versión de la norma, si se conoce.
        referencia: Tabla, artículo o cláusula de procedencia, si se conoce.

    Raises:
        EntradaCatalogoInvalida: Si el nombre está vacío o si los metadatos no
            son coherentes con el origen.
    """

    nombre: str
    origen: OrigenEntrada
    valor: T
    norma: NormId | None = None
    edicion: str | None = None
    referencia: str | None = None

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise EntradaCatalogoInvalida(
                "El nombre de una entrada del catálogo no puede estar vacío."
            )
        if self.origen is OrigenEntrada.NORMATIVO:
            if self.norma is None:
                raise EntradaCatalogoInvalida(
                    "Una entrada normativa debe indicar la norma de la que "
                    "procede."
                )
        elif (
            self.norma is not None
            or self.edicion is not None
            or self.referencia is not None
        ):
            raise EntradaCatalogoInvalida(
                "Una entrada de usuario no puede tener metadatos normativos."
            )
        if self.edicion is not None and not self.edicion.strip():
            raise EntradaCatalogoInvalida(
                "La edición de una entrada normativa no puede estar vacía."
            )
        if self.referencia is not None and not self.referencia.strip():
            raise EntradaCatalogoInvalida(
                "La referencia de una entrada normativa no puede estar vacía."
            )
