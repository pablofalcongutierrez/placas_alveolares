"""Geometría efectiva de componentes con huecos por elementos embebidos."""

from __future__ import annotations

from placas_alveolares.domain.errores import GeometriaInvalida
from placas_alveolares.domain.model.geometria import (
    GeometriaContorno,
    contorno_contiene,
    contornos_se_solapan,
)
from placas_alveolares.domain.model.seccion import ComponenteSeccion


def geometria_efectiva(
    componente: ComponenteSeccion,
    componentes_activos: tuple[ComponenteSeccion, ...],
) -> GeometriaContorno:
    """Construye la geometría de un componente descontando sus embebidos.

    Args:
        componente: Componente cuya geometría se prepara.
        componentes_activos: Componentes activos en la fase.

    Returns:
        La geometría exterior con sus huecos propios y los huecos de los
        componentes activos que lo declaran como anfitrión.

    Raises:
        GeometriaInvalida: Si un hueco no está contenido o hay huecos solapados.
    """
    huecos = list(componente.geometria.huecos)
    for candidato in componentes_activos:
        if candidato.componente_anfitrion_id == componente.id:
            huecos.append(candidato.geometria.exterior)

    for hueco in huecos:
        if not contorno_contiene(hueco, componente.geometria.exterior):
            raise GeometriaInvalida(
                f"Un hueco del componente '{componente.id}' no está contenido "
                "en su contorno exterior."
            )
    for i, primero in enumerate(huecos):
        for segundo in huecos[i + 1 :]:
            if contornos_se_solapan(primero, segundo):
                raise GeometriaInvalida(
                    f"El componente '{componente.id}' tiene huecos solapados."
                )

    return GeometriaContorno(
        exterior=componente.geometria.exterior,
        huecos=tuple(huecos),
    )
