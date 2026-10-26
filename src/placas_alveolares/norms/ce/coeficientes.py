"""Coeficientes parciales de seguridad del Código Estructural.

La tabla recoge los juegos de coeficientes ``γc`` y ``γs`` para los estados
límite últimos. Como el resto de tablas normativas, es dato abierto: añadir un
juego es añadir una línea.

Referencia de cláusula provisional: confirmar los valores y su articulado
contra la versión vigente del Código Estructural.
"""

from __future__ import annotations

from placas_alveolares.domain.value_objects.coeficientes_parciales import (
    CoeficientesParciales,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance

COEFICIENTES_CE: dict[str, CoeficientesParciales] = {
    "CE persistente o transitoria": CoeficientesParciales(
        gamma_c=1.5, gamma_s=1.15
    ),
    "CE accidental": CoeficientesParciales(gamma_c=1.3, gamma_s=1.0),
}
"""Juegos de coeficientes parciales de seguridad del Código Estructural."""


def tipos_coeficientes() -> tuple[str, ...]:
    """Nombres de los juegos de coeficientes disponibles.

    Returns:
        Las designaciones de la tabla, en el orden en que se declaran.
    """
    return tuple(COEFICIENTES_CE)


def coeficientes(nombre: str) -> CoeficientesParciales:
    """Devuelve el juego de coeficientes de una situación de cálculo.

    Args:
        nombre: Designación del juego (p. ej. ``"CE persistente o
            transitoria"``).

    Returns:
        Los coeficientes parciales del juego.

    Raises:
        CasoFueraDeAlcance: Si la designación no figura en la tabla.
    """
    try:
        return COEFICIENTES_CE[nombre]
    except KeyError as error:
        raise CasoFueraDeAlcance(
            f"El juego de coeficientes '{nombre}' no figura en la tabla del "
            f"Código Estructural. Disponibles: {', '.join(COEFICIENTES_CE)}."
        ) from error
