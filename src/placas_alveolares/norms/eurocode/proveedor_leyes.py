"""Proveedor de leyes constitutivas de cálculo del Eurocódigo 2.

El proveedor implementa el contrato :class:`ProveedorLeyes` del dominio para
análisis en estado límite último. La configuración es dato: los coeficientes
parciales y el diagrama elegido dentro de cada familia material determinan las
leyes que se inyectan en los motores mecánicos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import assert_never

from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    AceroPretensado,
    Hormigon,
)
from placas_alveolares.domain.model.seccion import ComponenteSeccion
from placas_alveolares.domain.value_objects.coeficientes_parciales import (
    CoeficientesParciales,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance
from placas_alveolares.norms.eurocode.laws import (
    ley_acero_pasivo_bilineal,
    ley_acero_pasivo_endurecida,
    ley_hormigon_bilineal,
    ley_hormigon_parabola,
)


class DiagramaHormigonELU(StrEnum):
    """Diagramas de cálculo del hormigón admitidos en ELU."""

    PARABOLA_RECTANGULO = "parabola_rectangulo"
    BILINEAL = "bilineal"


class DiagramaAceroPasivoELU(StrEnum):
    """Diagramas de cálculo del acero pasivo admitidos en ELU."""

    BILINEAL = "bilineal"
    ENDURECIDA = "endurecida"


def _coeficientes_recomendados() -> CoeficientesParciales:
    """Coeficientes parciales recomendados por EN 1992-1-1."""
    return CoeficientesParciales(gamma_c=1.5, gamma_s=1.15)


@dataclass(frozen=True, slots=True)
class ConfiguracionLeyesELUEurocodigo:
    """Configuración de las leyes de cálculo del Eurocódigo 2 en ELU.

    Attributes:
        coeficientes: Coeficientes parciales de seguridad de los materiales.
        diagrama_hormigon: Diagrama de cálculo del hormigón.
        diagrama_acero_pasivo: Diagrama de cálculo del acero pasivo.
    """

    coeficientes: CoeficientesParciales = field(
        default_factory=_coeficientes_recomendados
    )
    diagrama_hormigon: DiagramaHormigonELU = (
        DiagramaHormigonELU.PARABOLA_RECTANGULO
    )
    diagrama_acero_pasivo: DiagramaAceroPasivoELU = (
        DiagramaAceroPasivoELU.BILINEAL
    )


@dataclass(frozen=True, slots=True)
class ProveedorLeyesELUEurocodigo:
    """Proveedor de leyes constitutivas de cálculo de EN 1992-1-1.

    Attributes:
        configuracion: Coeficientes y diagramas que definen las leyes.
    """

    configuracion: ConfiguracionLeyesELUEurocodigo = field(
        default_factory=ConfiguracionLeyesELUEurocodigo
    )

    def ley_para(
        self,
        componente: ComponenteSeccion,
        fase: Fase,
    ) -> LeyTensionDeformacion:
        """Devuelve la ley de cálculo ELU de un componente.

        Args:
            componente: Componente del modelo.
            fase: Fase para la que se prepara la ley. Todavía no modifica las
                leyes porque el cálculo de fluencia y retracción queda fuera
                del alcance actual.

        Returns:
            La ley tensión-deformación de cálculo aplicable.

        Raises:
            CasoFueraDeAlcance: Si el componente es de acero de pretensado,
                para el que aún no existe un diagrama ELU completo, o si el
                acero pasivo no tiene rama plástica con los parámetros dados.
        """
        match componente.material:
            case Hormigon() as hormigon:
                return self._ley_hormigon(hormigon)
            case AceroArmadura() as acero:
                return self._ley_acero_pasivo(acero)
            case AceroPretensado():
                raise CasoFueraDeAlcance(
                    "El proveedor ELU del Eurocódigo no dispone todavía de "
                    "una ley de pretensado: AceroPretensado solo contiene "
                    "fpk y ep, insuficientes para definir el diagrama de "
                    f"cálculo del componente '{componente.id}'."
                )
            case _ as material:
                assert_never(material)

    def _ley_hormigon(self, hormigon: Hormigon) -> LeyTensionDeformacion:
        """Selecciona el diagrama de cálculo del hormigón."""
        gamma_c = self.configuracion.coeficientes.gamma_c
        match self.configuracion.diagrama_hormigon:
            case DiagramaHormigonELU.PARABOLA_RECTANGULO:
                return ley_hormigon_parabola(hormigon, gamma_c)
            case DiagramaHormigonELU.BILINEAL:
                return ley_hormigon_bilineal(hormigon, gamma_c)
            case _ as diagrama:
                assert_never(diagrama)

    def _ley_acero_pasivo(
        self,
        acero: AceroArmadura,
    ) -> LeyTensionDeformacion:
        """Selecciona el diagrama de cálculo del acero pasivo."""
        gamma_s = self.configuracion.coeficientes.gamma_s
        match self.configuracion.diagrama_acero_pasivo:
            case DiagramaAceroPasivoELU.BILINEAL:
                return ley_acero_pasivo_bilineal(acero, gamma_s)
            case DiagramaAceroPasivoELU.ENDURECIDA:
                return ley_acero_pasivo_endurecida(acero, gamma_s)
            case _ as diagrama:
                assert_never(diagrama)
