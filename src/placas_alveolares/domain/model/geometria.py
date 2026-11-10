"""Geometría de la sección transversal.

La sección se describe en un plano ``y-z`` ligado a la pieza: ``y`` horizontal
positivo hacia la derecha y ``z`` vertical positivo hacia arriba (véase
``docs/specs/001-walking-skeleton-flexion-ce/bases_calculo.md``, §2).

Todos los componentes —incluidos los cordones de pretensado— son regiones
delimitadas por un :class:`Contorno`. Un cordón se representa como un círculo
poligonizado con ``n`` puntos (:func:`circulo`), de modo que el modelo
geométrico es uniforme y el mallado en triángulos no necesita casos especiales.

Las geometrías son **declarativas e independientes**: los componentes pueden
solaparse en el modelo (p. ej. el contorno circular de un cordón dentro del
contorno de hormigón) y es el motor de integración quien resuelve la
superposición. Por ello el área de los contornos se calcula en valor absoluto
(el orden de vértices no importa) y los huecos se restan explícitamente.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from placas_alveolares.domain.errores import GeometriaInvalida

_LADOS_MINIMOS = 3
_PUNTOS_CIRCULO_POR_DEFECTO = 16


@dataclass(frozen=True, slots=True)
class Punto:
    """Punto del plano de la sección.

    Attributes:
        y: Coordenada horizontal (mm), positiva hacia la derecha.
        z: Coordenada vertical (mm), positiva hacia arriba.
    """

    y: float
    z: float


@dataclass(frozen=True, slots=True)
class Contorno:
    """Polígono cerrado del plano de la sección.

    El contorno se cierra implícitamente uniendo el último vértice con el
    primero; el sentido de recorrido es indiferente, ya que las áreas se
    calculan en valor absoluto.

    Attributes:
        puntos: Vértices del contorno, en orden.

    Raises:
        GeometriaInvalida: Si el contorno tiene menos de tres vértices.
    """

    puntos: tuple[Punto, ...]

    def __post_init__(self) -> None:
        if len(self.puntos) < _LADOS_MINIMOS:
            raise GeometriaInvalida(
                f"Un contorno necesita al menos {_LADOS_MINIMOS} vértices; "
                f"se recibieron {len(self.puntos)}."
            )


@dataclass(frozen=True, slots=True)
class GeometriaContorno:
    """Región material delimitada por un contorno exterior y sus huecos.

    Attributes:
        exterior: Contorno exterior de la región.
        huecos: Huecos interiores a descontar (p. ej. alveolos o vainos), por
            defecto ninguno.
    """

    exterior: Contorno
    huecos: tuple[Contorno, ...] = ()


def rectangulo(
    ancho: float,
    alto: float,
    *,
    y_centro: float = 0.0,
    z_base: float = 0.0,
) -> GeometriaContorno:
    """Construye un contorno rectangular.

    Args:
        ancho: Dimensión horizontal del rectángulo (mm).
        alto: Dimensión vertical del rectángulo (mm).
        y_centro: Coordenada horizontal del centro del rectángulo (mm). Por
            defecto ``0.0``.
        z_base: Cota de la base del rectángulo (mm). Por defecto ``0.0``.

    Returns:
        Una :class:`GeometriaContorno` rectangular sin huecos, centrada en
        ``y = y_centro`` y con base en ``z_base``.

    Raises:
        GeometriaInvalida: Si ``ancho`` o ``alto`` no son estrictamente
            positivos.
    """
    if ancho <= 0.0:
        raise GeometriaInvalida(
            "El ancho del rectángulo debe ser positivo; se recibió "
            f"ancho={ancho}."
        )
    if alto <= 0.0:
        raise GeometriaInvalida(
            "El alto del rectángulo debe ser positivo; se recibió "
            f"alto={alto}."
        )
    semiancho = ancho / 2.0
    z_sup = z_base + alto
    y_izq = y_centro - semiancho
    y_der = y_centro + semiancho
    exterior = Contorno(
        puntos=(
            Punto(y=y_izq, z=z_base),
            Punto(y=y_der, z=z_base),
            Punto(y=y_der, z=z_sup),
            Punto(y=y_izq, z=z_sup),
        )
    )
    return GeometriaContorno(exterior=exterior)


def circulo(
    centro: Punto, radio: float, *, n_puntos: int = _PUNTOS_CIRCULO_POR_DEFECTO
) -> GeometriaContorno:
    """Construye un círculo poligonizado con ``n_puntos`` vértices.

    El polígono queda **inscrito** en la circunferencia, por lo que su área
    subestima la del círculo (≈ 2,5 % con el valor por defecto de 16 puntos).
    Este error es de poligonización, no de integración: la cuadratura es exacta
    sobre cada triángulo del mallado.

    Args:
        centro: Centro del círculo (mm).
        radio: Radio del círculo (mm). Debe ser estrictamente positivo.
        n_puntos: Número de vértices del polígono. Por defecto 16.

    Returns:
        Una :class:`GeometriaContorno` circular sin huecos.

    Raises:
        GeometriaInvalida: Si ``radio`` no es positivo o ``n_puntos`` es menor
            que 3.
    """
    if radio <= 0.0:
        raise GeometriaInvalida(f"El radio debe ser positivo; se recibió {radio}.")
    if n_puntos < _LADOS_MINIMOS:
        raise GeometriaInvalida(
            f"Un círculo necesita al menos {_LADOS_MINIMOS} puntos; "
            f"se recibieron {n_puntos}."
        )
    paso = 2.0 * math.pi / n_puntos
    exterior = Contorno(
        puntos=tuple(
            Punto(
                y=centro.y + radio * math.cos(i * paso),
                z=centro.z + radio * math.sin(i * paso),
            )
            for i in range(n_puntos)
        )
    )
    return GeometriaContorno(exterior=exterior)


def area_contorno(contorno: Contorno) -> float:
    """Área de un contorno poligonal cerrado.

    Args:
        contorno: Contorno del que se calcula el área.

    Returns:
        El área en mm², independientemente del sentido de recorrido.
    """
    puntos = contorno.puntos
    doble_area = sum(
        puntos[i].y * puntos[(i + 1) % len(puntos)].z
        - puntos[(i + 1) % len(puntos)].y * puntos[i].z
        for i in range(len(puntos))
    )
    return abs(doble_area) / 2.0


def area_geometria(geometria: GeometriaContorno) -> float:
    """Área neta de una región, descontando sus huecos.

    Args:
        geometria: Región delimitada por un contorno exterior y sus huecos.

    Returns:
        El área neta en mm².
    """
    return area_contorno(geometria.exterior) - sum(
        area_contorno(hueco) for hueco in geometria.huecos
    )


def _producto_vectorial(a: Punto, b: Punto, c: Punto) -> float:
    """Producto vectorial ``(b−a) × (c−a)``."""
    return (b.y - a.y) * (c.z - a.z) - (b.z - a.z) * (c.y - a.y)


def _punto_en_segmento(punto: Punto, inicio: Punto, fin: Punto) -> bool:
    """Indica si un punto está sobre un segmento, incluidos sus extremos."""
    if abs(_producto_vectorial(inicio, fin, punto)) > 1.0e-9:
        return False
    return (
        min(inicio.y, fin.y) - 1.0e-9
        <= punto.y
        <= max(inicio.y, fin.y) + 1.0e-9
        and min(inicio.z, fin.z) - 1.0e-9
        <= punto.z
        <= max(inicio.z, fin.z) + 1.0e-9
    )


def punto_en_contorno(
    punto: Punto,
    contorno: Contorno,
    *,
    incluir_borde: bool = True,
) -> bool:
    """Comprueba si un punto está dentro de un contorno poligonal.

    Args:
        punto: Punto a comprobar.
        contorno: Polígono de referencia.
        incluir_borde: Si es ``True``, los puntos del borde cuentan como
            interiores. Por defecto ``True``.

    Returns:
        ``True`` si el punto pertenece a la región del contorno.
    """
    puntos = contorno.puntos
    for i, inicio in enumerate(puntos):
        fin = puntos[(i + 1) % len(puntos)]
        if _punto_en_segmento(punto, inicio, fin):
            return incluir_borde

    dentro = False
    for i, inicio in enumerate(puntos):
        fin = puntos[(i + 1) % len(puntos)]
        if (inicio.z > punto.z) != (fin.z > punto.z):
            y_corte = inicio.y + (punto.z - inicio.z) * (
                fin.y - inicio.y
            ) / (fin.z - inicio.z)
            if punto.y < y_corte:
                dentro = not dentro
    return dentro


def _segmentos_se_cruzan(
    a: Punto,
    b: Punto,
    c: Punto,
    d: Punto,
) -> bool:
    """Indica si dos segmentos se cruzan en un punto interior."""
    d1 = _producto_vectorial(c, d, a)
    d2 = _producto_vectorial(c, d, b)
    d3 = _producto_vectorial(a, b, c)
    d4 = _producto_vectorial(a, b, d)
    return (
        ((d1 > 0.0 and d2 < 0.0) or (d1 < 0.0 and d2 > 0.0))
        and ((d3 > 0.0 and d4 < 0.0) or (d3 < 0.0 and d4 > 0.0))
    )


def _contornos_tienen_cruces(
    primero: Contorno,
    segundo: Contorno,
) -> bool:
    """Indica si las aristas de dos contornos se cruzan propiamente."""
    puntos_primero = primero.puntos
    puntos_segundo = segundo.puntos
    for i, a in enumerate(puntos_primero):
        b = puntos_primero[(i + 1) % len(puntos_primero)]
        for j, c in enumerate(puntos_segundo):
            d = puntos_segundo[(j + 1) % len(puntos_segundo)]
            if _segmentos_se_cruzan(a, b, c, d):
                return True
    return False


def contorno_contiene(interior: Contorno, exterior: Contorno) -> bool:
    """Comprueba si un contorno está íntegramente dentro de otro.

    El contacto con el borde exterior está permitido.

    Args:
        interior: Contorno que se supone contenido.
        exterior: Contorno contenedor.

    Returns:
        ``True`` si todos los puntos de ``interior`` pertenecen a ``exterior``
        y no hay cruces entre sus aristas.
    """
    if not all(
        punto_en_contorno(punto, exterior) for punto in interior.puntos
    ):
        return False
    return not _contornos_tienen_cruces(interior, exterior)


def _puntos_de_muestreo(contorno: Contorno) -> tuple[Punto, ...]:
    """Devuelve vértices y puntos medios de las aristas de un contorno."""
    puntos = contorno.puntos
    muestras: list[Punto] = list(puntos)
    for i, inicio in enumerate(puntos):
        fin = puntos[(i + 1) % len(puntos)]
        muestras.append(
            Punto(
                y=(inicio.y + fin.y) / 2.0,
                z=(inicio.z + fin.z) / 2.0,
            )
        )
    return tuple(muestras)


def contornos_se_solapan(primero: Contorno, segundo: Contorno) -> bool:
    """Indica si dos contornos tienen área en común.

    El contacto simple de bordes no cuenta como solape.

    Args:
        primero: Primer contorno.
        segundo: Segundo contorno.

    Returns:
        ``True`` si uno contiene al otro o si sus áreas se cruzan.
    """
    if contorno_contiene(primero, segundo) or contorno_contiene(
        segundo, primero
    ):
        return True
    if _contornos_tienen_cruces(primero, segundo):
        return True
    return any(
        punto_en_contorno(punto, segundo, incluir_borde=False)
        for punto in _puntos_de_muestreo(primero)
    ) or any(
        punto_en_contorno(punto, primero, incluir_borde=False)
        for punto in _puntos_de_muestreo(segundo)
    )
