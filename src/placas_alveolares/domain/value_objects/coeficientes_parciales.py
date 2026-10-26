"""Coeficientes parciales de seguridad de un estado límite último.

El dominio define la **forma** del juego de coeficientes; los **valores** son
dato normativo y viven en ``norms/*/coeficientes.py`` (ADR 0001). Esta
separación permite que la biblioteca de usuario los trate como datos
intercambiables sin acoplar el núcleo a ninguna norma.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.errores import CoeficientesInvalidos


@dataclass(frozen=True, slots=True)
class CoeficientesParciales:
    """Coeficientes parciales de seguridad de materiales.

    Attributes:
        gamma_c: Coeficiente parcial del hormigón.
        gamma_s: Coeficiente parcial del acero.

    Raises:
        CoeficientesInvalidos: Si algún coeficiente no es estrictamente
            positivo.
    """

    gamma_c: float
    gamma_s: float

    def __post_init__(self) -> None:
        if self.gamma_c <= 0.0:
            raise CoeficientesInvalidos(
                "El coeficiente parcial del hormigón gamma_c debe ser "
                f"positivo; se recibió {self.gamma_c}."
            )
        if self.gamma_s <= 0.0:
            raise CoeficientesInvalidos(
                "El coeficiente parcial del acero gamma_s debe ser positivo; "
                f"se recibió {self.gamma_s}."
            )
