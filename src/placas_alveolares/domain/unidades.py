"""Convención de unidades del núcleo de cálculo.

Todo el núcleo trabaja en un sistema coherente fijo:

- longitud en **milímetros** (mm),
- fuerza en **newtons** (N),
- tensión en **megapascales** (MPa = N/mm²),
- momento en **newtons·milímetro** (N·mm).

Las conversiones se realizan únicamente en las fronteras (interfaz de
usuario, importación y exportación); dentro del dominio nunca se cambia de
unidad. Véase ``docs/decisions/0004-unidades-convencion-n-mm-mpa.md``.
"""

from __future__ import annotations

N_POR_KN: float = 1_000.0
"""Factor de conversión de kilonewtons a newtons."""

MM_POR_M: float = 1_000.0
"""Factor de conversión de metros a milímetros."""

KN_M_A_N_MM: float = 1_000_000.0
"""Factor de conversión de kN·m a N·mm (10⁶)."""
