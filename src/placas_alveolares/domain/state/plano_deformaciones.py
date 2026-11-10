"""Plano de deformaciones de una sección transversal.

El plano describe la distribución lineal de la deformación longitudinal
(hipótesis de Bernoulli–Navier):

``ε(y, z) = ε₀ + κ_y·z − κ_z·y``

Las deformaciones son positivas a tracción. El mismo tipo representa tanto el
estado inicial de un componente como el incremento común que se resuelve en un
análisis, de modo que la deformación total de una fibra es la suma de ambos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlanoDeformaciones:
    """Plano lineal de deformaciones longitudinales.

    Attributes:
        eps0: Deformación en el origen de la sección (tanto por uno).
        kappa_y: Curvatura alrededor del eje ``y`` (mm⁻¹).
        kappa_z: Curvatura alrededor del eje ``z`` (mm⁻¹).
    """

    eps0: float
    kappa_y: float
    kappa_z: float

    def deformacion(self, y: float, z: float) -> float:
        """Deformación longitudinal de una fibra.

        Args:
            y: Coordenada horizontal de la fibra (mm).
            z: Coordenada vertical de la fibra (mm).

        Returns:
            La deformación longitudinal (tanto por uno), positiva a tracción.
        """
        return self.eps0 + self.kappa_y * z - self.kappa_z * y

    def __add__(self, otro: PlanoDeformaciones) -> PlanoDeformaciones:
        """Suma dos planos de deformaciones.

        Args:
            otro: Plano que se suma al actual.

        Returns:
            Un plano con la suma componente a componente.
        """
        return PlanoDeformaciones(
            eps0=self.eps0 + otro.eps0,
            kappa_y=self.kappa_y + otro.kappa_y,
            kappa_z=self.kappa_z + otro.kappa_z,
        )

    def __sub__(self, otro: PlanoDeformaciones) -> PlanoDeformaciones:
        """Resta dos planos de deformaciones.

        Args:
            otro: Plano que se resta al actual.

        Returns:
            Un plano con la resta componente a componente.
        """
        return PlanoDeformaciones(
            eps0=self.eps0 - otro.eps0,
            kappa_y=self.kappa_y - otro.kappa_y,
            kappa_z=self.kappa_z - otro.kappa_z,
        )


PLANO_NULO = PlanoDeformaciones(eps0=0.0, kappa_y=0.0, kappa_z=0.0)
"""Plano sin deformación, usado como valor por defecto."""
