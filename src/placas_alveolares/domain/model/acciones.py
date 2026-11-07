"""Acciones internas sobre una sección.

Convención de signos (véase ``bases_calculo.md``, §2). Todos los sentidos se
definen sobre la cara de normal ``+x`` (la que mira hacia el observador); en la
cara ``-x`` se invierten:

- Esfuerzo axil ``n`` positivo a **tracción** (fuerza hacia ``+x``).
- Cortante ``v_y`` positivo hacia ``+y`` (derecha).
- Cortante ``v_z`` positivo hacia ``-z`` (abajo).
- Momento ``m_y`` positivo cuando produce tracción en las fibras inferiores
  (``z < 0``).
- Momento ``m_z`` positivo cuando produce tracción en las fibras con ``y > 0``.

Con esta convención se cumple ``dm_y/dx = v_z`` y ``dm_z/dx = v_y``. Si se
integran tensiones tangenciales, ``v_y = ∫τ_xy dA`` y ``v_z = −∫τ_xz dA``,
porque ``z`` es positivo hacia arriba.

La barra es tridimensional: el modelo contempla axil, cortante biaxial y
flexión biaxial. El torsor se añadirá de forma aditiva cuando la comprobación
correspondiente lo necesite.
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
        v_y: Cortante horizontal (N), positivo hacia ``+y`` sobre la cara
            ``+x``. Por defecto ``0.0``.
        v_z: Cortante vertical (N), positivo hacia ``-z`` (abajo) sobre la cara
            ``+x``. Por defecto ``0.0``.
    """

    n: float = 0.0
    m_y: float = 0.0
    m_z: float = 0.0
    v_y: float = 0.0
    v_z: float = 0.0
