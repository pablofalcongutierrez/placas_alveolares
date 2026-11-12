"""Alineación de una sección con la línea neutra de un plano de deformaciones.

La representación habitual de una sección en flexión coloca la línea neutra
horizontal para poder compartir la misma cota vertical entre la sección, el
diagrama de deformaciones y el diagrama de tensiones.

Para un plano ``ε(y, z) = ε₀ + κ_y·z − κ_z·y``, el gradiente de deformación
es ``(−κ_z, κ_y)``. El sistema alineado ``(u, v)`` se define con:

- ``u``: dirección tangente a la línea neutra;
- ``v``: dirección normal, positiva hacia el aumento de deformación.

Con ``κ = hypot(κ_y, κ_z)``, la transformación es una rotación:

``u = cos(θ)·y + sen(θ)·z``
``v = −sen(θ)·y + cos(θ)·z − v_LN``

donde ``cos(θ) = κ_y/κ``, ``sen(θ) = κ_z/κ`` y ``v_LN = −ε₀/κ``. Con ello la
deformación del plano común queda ``ε = κ·v`` y la línea neutra en ``v = 0``.

Este módulo contiene **solo geometría mecánica**. No conoce colores, escalas,
píxeles ni ninguna tecnología de presentación.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.model.geometria import Punto
from placas_alveolares.domain.state.plano_deformaciones import (
    PlanoDeformaciones,
)

_CURVATURA_MINIMA = 1.0e-12
"""Curvatura (mm⁻¹) por debajo de la cual no se define línea neutra."""


@dataclass(frozen=True, slots=True)
class PuntoAlineado:
    """Punto expresado en el sistema alineado con la línea neutra.

    Attributes:
        u: Coordenada tangente a la línea neutra (mm).
        v: Coordenada normal a la línea neutra (mm), positiva hacia el
            aumento de deformación.
    """

    u: float
    v: float


@dataclass(frozen=True, slots=True)
class SistemaReferenciaAlineado:
    """Sistema girado que deja horizontal la línea neutra de un plano.

    Attributes:
        eps0: Deformación del plano en el origen original.
        curvatura: Módulo de la curvatura resultante (mm⁻¹).
        coseno: Coseno del ángulo de giro.
        seno: Seno del ángulo de giro.
        cota_linea_neutra: Cota ``q`` de la línea neutra en el sistema girado
            antes de trasladar el origen (mm). Es ``0.0`` cuando la línea no
            está definida.
        linea_neutra_definida: Indica si existe una línea neutra única. Es
            ``False`` cuando la curvatura es despreciable.
    """

    eps0: float
    curvatura: float
    coseno: float
    seno: float
    cota_linea_neutra: float
    linea_neutra_definida: bool

    @property
    def angulo_radianes(self) -> float:
        """Ángulo de giro del sistema alineado (rad)."""
        return math.atan2(self.seno, self.coseno)

    def a_alineado(self, punto: Punto) -> PuntoAlineado:
        """Transforma un punto de la sección al sistema alineado.

        Args:
            punto: Punto en coordenadas ``(y, z)`` de la sección (mm).

        Returns:
            El mismo punto en coordenadas ``(u, v)`` (mm).
        """
        u = self.coseno * punto.y + self.seno * punto.z
        q = -self.seno * punto.y + self.coseno * punto.z
        return PuntoAlineado(u=u, v=q - self.cota_linea_neutra)

    def a_seccion(self, punto: PuntoAlineado) -> Punto:
        """Transforma un punto alineado a coordenadas de la sección.

        Args:
            punto: Punto en coordenadas ``(u, v)`` (mm).

        Returns:
            El mismo punto en coordenadas ``(y, z)`` (mm).
        """
        q = punto.v + self.cota_linea_neutra
        return Punto(
            y=self.coseno * punto.u - self.seno * q,
            z=self.seno * punto.u + self.coseno * q,
        )

    def deformacion_comun(self, v: float) -> float:
        """Deformación del plano común en una cota alineada.

        Args:
            v: Coordenada normal a la línea neutra (mm).

        Returns:
            La deformación longitudinal (tanto por uno), positiva a tracción.
        """
        if not self.linea_neutra_definida:
            return self.eps0
        return self.curvatura * v


def sistema_referencia_alineado(
    plano: PlanoDeformaciones,
    tolerancia_curvatura: float = _CURVATURA_MINIMA,
) -> SistemaReferenciaAlineado:
    """Construye el sistema que deja horizontal la línea neutra del plano.

    Si la curvatura resultante es menor que ``tolerancia_curvatura`` no existe
    una dirección de línea neutra única. En ese caso se conserva la orientación
    original y se marca ``linea_neutra_definida`` como ``False``.

    Args:
        plano: Plano de deformaciones que se desea alinear.
        tolerancia_curvatura: Umbral de curvatura (mm⁻¹) por debajo del cual se
            considera que el plano no define línea neutra. Por defecto
            ``1.0e-12``.

    Returns:
        El sistema de referencia alineado.

    Raises:
        ErrorValidacion: Si el plano no es finito o la tolerancia es negativa.
    """
    if not all(
        math.isfinite(valor)
        for valor in (plano.eps0, plano.kappa_y, plano.kappa_z)
    ):
        raise ErrorValidacion(
            "El plano de deformaciones debe contener valores finitos."
        )
    if not math.isfinite(tolerancia_curvatura) or tolerancia_curvatura < 0.0:
        raise ErrorValidacion(
            "La tolerancia de curvatura debe ser finita y no negativa; se "
            f"recibió {tolerancia_curvatura}."
        )
    curvatura = math.hypot(plano.kappa_y, plano.kappa_z)
    if curvatura <= tolerancia_curvatura:
        return SistemaReferenciaAlineado(
            eps0=plano.eps0,
            curvatura=0.0,
            coseno=1.0,
            seno=0.0,
            cota_linea_neutra=0.0,
            linea_neutra_definida=False,
        )

    coseno = plano.kappa_y / curvatura
    seno = plano.kappa_z / curvatura
    return SistemaReferenciaAlineado(
        eps0=plano.eps0,
        curvatura=curvatura,
        coseno=coseno,
        seno=seno,
        cota_linea_neutra=-plano.eps0 / curvatura,
        linea_neutra_definida=True,
    )
