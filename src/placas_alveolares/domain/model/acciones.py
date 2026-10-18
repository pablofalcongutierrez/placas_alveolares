"""Acciones internas sobre una sección.

Convención de signos (véase ``bases_calculo.md``, §2):

- Esfuerzo axil ``n`` positivo a **tracción**.
- Momento ``m_y`` (alrededor de la horizontal) positivo cuando produce tracción
  en las fibras inferiores (``z < 0``).
- Momento ``m_z`` (alrededor de la vertical) positivo cuando produce tracción
  en las fibras con ``y > 0``.

La barra es tridimensional: el modelo contempla axil y flexión **biaxial**. Los
esfuerzos cortantes y el torsor se añadirán de forma aditiva cuando los checks
correspondientes los necesiten.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EsfuerzosInternos:
    """Esfuerzos internos de cálculo sobre la sección.

    Attributes:
        n: Esfuerzo axil (N), positivo a tracción. Por defecto ``0.0``.
        m_y: Momento flector alrededor del eje horizontal ``y`` (N·mm).
            Por defecto ``0.0``.
        m_z: Momento flector alrededor del eje vertical ``z`` (N·mm).
            Por defecto ``0.0``.
    """

    n: float = 0.0
    m_y: float = 0.0
    m_z: float = 0.0
