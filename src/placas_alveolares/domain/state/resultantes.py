"""Resultantes de tensiones sobre una sección transversal."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResultantesSeccion:
    """Resultantes de las tensiones normales.

    Attributes:
        n: Esfuerzo axil resultante (N), positivo a tracción.
        m_y: Momento flector alrededor del eje ``y`` (N·mm); positivo cuando
            produce tracción en ``z < 0``.
        m_z: Momento flector alrededor del eje ``z`` (N·mm); positivo cuando
            produce tracción en ``y > 0``.
    """

    n: float
    m_y: float
    m_z: float
