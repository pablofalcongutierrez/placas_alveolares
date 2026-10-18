"""Propiedades geométricas de una región de contorno.

Las propiedades se calculan por **mallado en triángulos + cuadratura de
Gauss**: el área, los momentos estáticos y los momentos de inercia son
integrales de un campo escalar sobre la región. El mismo motor servirá para
integrar tensiones cuando se incorpore el solver general por fibras.

La sección trabaja en el plano ``y-z`` y la respuesta es **biaxial**: se
calculan el centro de gravedad en ambos ejes, la inercia respecto a cada eje y
el producto de inercia (acoplamiento). Con la regla de tres puntos (por
defecto), todos estos valores son **exactos** para contornos poligonales: la
regla es exacta para polinomios de grado ≤ 2. No se conoce ningún material ni
fase: la región se trata como homogénea.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.mechanics.integracion import (
    REGLA_3_PUNTOS,
    ReglaCuadratura,
    integrar,
)
from placas_alveolares.domain.mechanics.mallado import mallar
from placas_alveolares.domain.model.geometria import GeometriaContorno


@dataclass(frozen=True, slots=True)
class PropiedadesSeccion:
    """Propiedades geométricas de una región.

    Attributes:
        area: Área de la región (mm²).
        y_cdg: Coordenada horizontal del centro de gravedad (mm).
        z_cdg: Coordenada vertical del centro de gravedad (mm).
        i_y: Momento de inercia respecto a la horizontal que pasa por el centro
            de gravedad (mm⁴): ``∫ (z − z_cdg)² dA``.
        i_z: Momento de inercia respecto a la vertical que pasa por el centro de
            gravedad (mm⁴): ``∫ (y − y_cdg)² dA``.
        i_yz: Producto de inercia respecto a los ejes que pasan por el centro de
            gravedad (mm⁴): ``∫ (y − y_cdg)(z − z_cdg) dA``.
    """

    area: float
    y_cdg: float
    z_cdg: float
    i_y: float
    i_z: float
    i_yz: float


def propiedades_geometricas(
    geometria: GeometriaContorno,
    regla: ReglaCuadratura = REGLA_3_PUNTOS,
) -> PropiedadesSeccion:
    """Propiedades geométricas de una región con huecos.

    Args:
        geometria: Región definida por un contorno exterior y sus huecos.
        regla: Regla de cuadratura. Por defecto la de tres puntos, exacta para
            polinomios de grado ≤ 2 (inercias exactas).

    Returns:
        Las propiedades geométricas de la región neta.

    Raises:
        ValueError: Si el área de la región no es estrictamente positiva.
    """
    malla = mallar(geometria)
    area = integrar(malla, lambda _: 1.0, regla)
    if area <= 0.0:
        raise ValueError("El área de la región no es positiva; revise la geometría.")

    y_cdg = integrar(malla, lambda punto: punto.y, regla) / area
    z_cdg = integrar(malla, lambda punto: punto.z, regla) / area
    i_y = integrar(malla, lambda punto: (punto.z - z_cdg) ** 2, regla)
    i_z = integrar(malla, lambda punto: (punto.y - y_cdg) ** 2, regla)
    i_yz = integrar(
        malla, lambda punto: (punto.y - y_cdg) * (punto.z - z_cdg), regla
    )
    return PropiedadesSeccion(
        area=area,
        y_cdg=y_cdg,
        z_cdg=z_cdg,
        i_y=i_y,
        i_z=i_z,
        i_yz=i_yz,
    )
