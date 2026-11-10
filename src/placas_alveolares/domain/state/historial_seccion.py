"""Historial inmutable de estados seccionales por fase."""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.errores import FaseInvalida
from placas_alveolares.domain.state.estado_seccion import EstadoSeccionFase


@dataclass(frozen=True, slots=True)
class HistorialSeccion:
    """Secuencia de estados de una sección, en orden de cálculo.

    Attributes:
        estados: Un estado por fase calculada, en el orden de la tupla de fases.

    Raises:
        FaseInvalida: Si hay índices de fase repetidos.
    """

    estados: tuple[EstadoSeccionFase, ...]

    def __post_init__(self) -> None:
        indices = [estado.fase for estado in self.estados]
        if len(set(indices)) != len(indices):
            raise FaseInvalida(
                "El historial no puede contener dos estados de la misma fase."
            )

    def estado(self, fase: int) -> EstadoSeccionFase:
        """Devuelve el estado de una fase.

        Args:
            fase: Índice de la fase buscada.

        Returns:
            El estado correspondiente.

        Raises:
            FaseInvalida: Si la fase no figura en el historial.
        """
        for estado in self.estados:
            if estado.fase == fase:
                return estado
        raise FaseInvalida(
            f"El historial no contiene la fase con índice {fase}."
        )

    @property
    def ultimo(self) -> EstadoSeccionFase:
        """Último estado calculado.

        Raises:
            FaseInvalida: Si el historial está vacío.
        """
        if not self.estados:
            raise FaseInvalida("El historial no contiene ningún estado.")
        return self.estados[-1]
