"""Proveedor de leyes elásticas lineales para análisis instantáneos."""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.mechanics.generic_laws import LeyElastica
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.materiales import modulo_elastico
from placas_alveolares.domain.model.seccion import ComponenteSeccion


@dataclass(frozen=True, slots=True)
class ProveedorLeyesElasticas:
    """Proveedor de leyes elásticas con el módulo de cada material.

    Se utiliza para análisis instantáneos sin efectos diferidos ni diagramas
    de cálculo normativos, como la transferencia de pretensado del alcance
    actual.
    """

    def ley_para(
        self,
        componente: ComponenteSeccion,
        fase: Fase,
    ) -> LeyTensionDeformacion:
        """Devuelve la ley elástica del material de un componente.

        Args:
            componente: Componente del modelo.
            fase: Fase para la que se prepara la ley. La ley elástica no
                depende de ella.

        Returns:
            La ley lineal con el módulo ``Ecm``, ``Es`` o ``Ep`` del material.
        """
        return LeyElastica(modulo_elastico(componente.material))
