"""Implementación en memoria del catálogo genérico de datos.

Separa dos colecciones: los presets normativos, recibidos por inyección y de
solo lectura, y las entradas de usuario, mutables. Los presets se identifican
por la clave compuesta ``(norma, nombre)``, de modo que dos normas pueden
compartir una misma designación sin sobrescribirse.
"""

from __future__ import annotations

from collections.abc import Iterable

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

type _ClaveNormativa = tuple[NormId, str]


class AlmacenCatalogo[T](Catalogo[T]):
    """Almacén tipado de entradas normativas y de usuario."""

    def __init__(
        self,
        normativos: Iterable[EntradaCatalogo[T]] | None = None,
    ) -> None:
        """Inicializa el almacén con los presets normativos.

        Args:
            normativos: Presets de solo lectura inyectados desde la norma.

        Raises:
            EntradaCatalogoInvalida: Si algún preset no tiene origen normativo
                o carece de norma.
            EntradaDuplicada: Si dos presets comparten norma y nombre.
        """
        self._normativos: dict[_ClaveNormativa, EntradaCatalogo[T]] = {}
        self._nombres_normativos: set[str] = set()
        self._usuarios: dict[str, EntradaCatalogo[T]] = {}

        for entrada in normativos or ():
            norma = entrada.norma
            if entrada.origen is not OrigenEntrada.NORMATIVO or norma is None:
                raise EntradaCatalogoInvalida(
                    "El almacén solo admite entradas normativas como presets; "
                    f"se recibió '{entrada.nombre}' con origen "
                    f"'{entrada.origen}'."
                )

            clave = (norma, entrada.nombre)
            if clave in self._normativos:
                raise EntradaDuplicada(
                    f"El preset '{entrada.nombre}' de la norma "
                    f"'{norma.value}' está registrado más de una vez."
                )

            self._normativos[clave] = entrada
            self._nombres_normativos.add(entrada.nombre)

    def listar(self) -> tuple[EntradaCatalogo[T], ...]:
        """Lista las entradas, primero las normativas y después las de usuario.

        Returns:
            Las entradas con su origen y procedencia.
        """
        normativos = tuple(self._normativos.values())
        usuarios = tuple(self._usuarios.values())
        return normativos + usuarios

    def listar_disponibles(
        self, norma: NormId
    ) -> tuple[EntradaCatalogo[T], ...]:
        """Lista los presets de una norma y todas las entradas de usuario.

        Args:
            norma: Norma de cálculo seleccionada.

        Returns:
            Los presets de la norma seguidos de las entradas de usuario.
        """
        normativos = tuple(
            entrada
            for entrada in self._normativos.values()
            if entrada.norma is norma
        )
        return normativos + tuple(self._usuarios.values())

    def obtener(self, nombre: str, *, norma: NormId | None = None) -> T | None:
        """Obtiene una entrada normativa o de usuario.

        Args:
            nombre: Clave de la entrada.
            norma: Norma del preset. Si es ``None``, busca una entrada de
                usuario.

        Returns:
            El valor o ``None`` si no existe.
        """
        if norma is None:
            entrada_usuario = self._usuarios.get(nombre)
            return (
                None
                if entrada_usuario is None
                else entrada_usuario.valor
            )

        entrada_normativa = self._normativos.get((norma, nombre))
        return (
            None
            if entrada_normativa is None
            else entrada_normativa.valor
        )

    def registrar(self, nombre: str, valor: T) -> None:
        """Registra o sustituye una entrada de usuario.

        Args:
            nombre: Clave de la entrada.
            valor: Valor a guardar.

        Raises:
            EntradaProtegida: Si el nombre coincide con un preset normativo.
            EntradaCatalogoInvalida: Si el nombre no es válido.
        """
        if nombre in self._nombres_normativos:
            raise EntradaProtegida(
                f"'{nombre}' coincide con una entrada normativa y no puede "
                "modificarse; cree una entrada de usuario con otro nombre."
            )
        entrada = EntradaCatalogo(
            nombre=nombre,
            origen=OrigenEntrada.USUARIO,
            valor=valor,
        )
        self._usuarios[nombre] = entrada

    def eliminar(self, nombre: str) -> None:
        """Elimina una entrada de usuario.

        Args:
            nombre: Clave de la entrada.

        Raises:
            EntradaProtegida: Si el nombre corresponde a un preset normativo.
        """
        if nombre in self._nombres_normativos:
            raise EntradaProtegida(
                f"'{nombre}' es una entrada normativa y no puede eliminarse."
            )
        self._usuarios.pop(nombre, None)
