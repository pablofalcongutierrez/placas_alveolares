"""Puerto genérico de un catálogo de datos normativos y de usuario.

El catálogo almacena un único tipo de dato por instancia. La selección entre
presets de distintas normas se realiza mediante :class:`NormId`, mientras que
las entradas de usuario son independientes de la norma.
"""

from __future__ import annotations

from typing import Protocol

from placas_alveolares.application.ports.entradas_catalogo import EntradaCatalogo
from placas_alveolares.domain.checking.kinds import NormId


class Catalogo[T](Protocol):
    """Contrato de una biblioteca tipada de datos.

    El parámetro ``T`` es invariante: aparece tanto en la consulta como en el
    registro, por lo que no puede declararse covariante.
    """

    def listar(self) -> tuple[EntradaCatalogo[T], ...]:
        """Lista todas las entradas del catálogo.

        Returns:
            Primero los presets normativos y después las entradas de usuario.
        """
        ...

    def listar_disponibles(
        self, norma: NormId
    ) -> tuple[EntradaCatalogo[T], ...]:
        """Lista las entradas utilizables con una norma.

        Args:
            norma: Norma de cálculo seleccionada.

        Returns:
            Los presets de esa norma seguidos de todas las entradas de usuario,
            que son independientes de la norma.
        """
        ...

    def obtener(self, nombre: str, *, norma: NormId | None = None) -> T | None:
        """Obtiene el valor de una entrada.

        Args:
            nombre: Clave de la entrada.
            norma: Norma del preset que se desea consultar. Si es ``None``, se
                consulta el espacio de entradas de usuario.

        Returns:
            El valor almacenado o ``None`` si no existe.
        """
        ...

    def registrar(self, nombre: str, valor: T) -> None:
        """Registra o sustituye una entrada de usuario.

        Args:
            nombre: Clave de la entrada.
            valor: Valor a guardar.

        Raises:
            EntradaProtegida: Si el nombre coincide con un preset normativo.
            EntradaCatalogoInvalida: Si el nombre no es válido.
        """
        ...

    def eliminar(self, nombre: str) -> None:
        """Elimina una entrada de usuario.

        Args:
            nombre: Clave de la entrada.

        Raises:
            EntradaProtegida: Si el nombre corresponde a un preset normativo.
        """
        ...
