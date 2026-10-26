"""Leyes constitutivas de la familia eurocódigo.

Se implementan las leyes tensión-deformación de EN 1992-1-1, compartidas por el
Código Estructural:

- Hormigón, cuatro leyes: lineal elástica (3.1.5), parábola-rectángulo
  (3.1.7(1), figura 3.3), bilineal (3.1.7(2), figura 3.4) y general no lineal
  (3.1.5, ecuación 3.14, figura 3.2).
- Acero pasivo, dos leyes de cálculo: bilineal con rama horizontal
  (3.2.7(2), figura 3.7b) y bilineal con endurecimiento o rama inclinada
  (3.2.7(1), figura 3.7a).

El Código Estructural adopta estas mismas leyes; la diferencia entre CE y EC2
son los coeficientes y las referencias de cláusula (ADR 0006).

Las leyes se construyen con los **valores ya resueltos** (``fcd``, ``εc2``…):
no consultan el modelo ni la norma desde el motor. Las factorías de este módulo
hacen esa resolución a partir de :class:`Hormigon` o :class:`AceroArmadura`
(ADR 0001).

Convención: deformaciones y tensiones positivas en tracción y negativas en
compresión; deformación adimensional (tanto por uno) y tensión en MPa. Las
deformaciones de la Tabla 3.1 se tabulan en ‰ y se convierten aquí a tanto por
uno.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.mechanics.generic_laws import (
    LeyElastica,
    LeyElastoplastica,
)
from placas_alveolares.domain.model.materiales import AceroArmadura, Hormigon
from placas_alveolares.norms.errores import CasoFueraDeAlcance

_FCK_MINIMO = 12.0
"""Resistencia característica mínima cubierta por la Tabla 3.1 (MPa)."""

_FCK_MAXIMO = 90.0
"""Resistencia característica máxima cubierta por la Tabla 3.1 (MPa)."""

_FACTOR_DEFORMACION_ULTIMA = 0.9
"""Factor de EN 1992-1-1, 3.2.7(2): ``εud = 0,9·εuk``."""


@dataclass(frozen=True, slots=True)
class DeformacionesHormigon:
    """Deformaciones características de los diagramas del hormigón.

    Valores de la Tabla 3.1 de EN 1992-1-1, en tanto por uno.

    Attributes:
        eps_c1: Deformación en la tensión máxima del diagrama general.
        eps_cu1: Deformación última del diagrama general.
        eps_c2: Deformación en la tensión máxima del diagrama parábola-rectángulo.
        eps_cu2: Deformación última del diagrama parábola-rectángulo.
        exponente: Exponente ``n`` del diagrama parábola-rectángulo.
        eps_c3: Deformación en la tensión máxima del diagrama bilineal.
        eps_cu3: Deformación última del diagrama bilineal.
    """

    eps_c1: float
    eps_cu1: float
    eps_c2: float
    eps_cu2: float
    exponente: float
    eps_c3: float
    eps_cu3: float


def deformaciones_tabla_3_1(fck: float, fcm: float) -> DeformacionesHormigon:
    """Deformaciones de los diagramas del hormigón según la Tabla 3.1.

    Args:
        fck: Resistencia característica a compresión (MPa).
        fcm: Resistencia media a compresión (MPa).

    Returns:
        Las deformaciones de los diagramas, en tanto por uno.

    Raises:
        CasoFueraDeAlcance: Si ``fck`` queda fuera del rango 12–90 MPa cubierto
            por la Tabla 3.1.
    """
    if not _FCK_MINIMO <= fck <= _FCK_MAXIMO:
        raise CasoFueraDeAlcance(
            "La Tabla 3.1 de EN 1992-1-1 cubre fck entre 12 y 90 MPa; "
            f"se recibió fck = {fck} MPa."
        )

    eps_c1 = min(0.7 * fcm**0.31, 2.8) / 1000.0
    if fck <= 50.0:
        return DeformacionesHormigon(
            eps_c1=eps_c1,
            eps_cu1=3.5 / 1000.0,
            eps_c2=2.0 / 1000.0,
            eps_cu2=3.5 / 1000.0,
            exponente=2.0,
            eps_c3=1.75 / 1000.0,
            eps_cu3=3.5 / 1000.0,
        )

    eps_cu2 = (2.6 + 35.0 * ((90.0 - fck) / 100.0) ** 4) / 1000.0
    
    return DeformacionesHormigon(
        eps_c1=eps_c1,
        eps_cu1=(2.8 + 27.0 * ((98.0 - fcm) / 100.0) ** 4) / 1000.0,
        eps_c2=(2.0 + 0.085 * (fck - 50.0) ** 0.53) / 1000.0,
        eps_cu2=eps_cu2,
        exponente=1.4 + 23.4 * ((90.0 - fck) / 100.0) ** 4,
        eps_c3=(1.75 + 0.55 * (fck - 50.0) / 40.0) / 1000.0,
        eps_cu3=eps_cu2,
    )


def fcm_tabla_3_1(fck: float) -> float:
    """Resistencia media a compresión según la Tabla 3.1.

    Args:
        fck: Resistencia característica a compresión (MPa).

    Returns:
        La resistencia media ``fcm = fck + 8`` (MPa).

    Raises:
        CasoFueraDeAlcance: Si ``fck`` queda fuera del rango 12–90 MPa
            cubierto por la Tabla 3.1.
    """
    if not _FCK_MINIMO <= fck <= _FCK_MAXIMO:
        raise CasoFueraDeAlcance(
            "La Tabla 3.1 de EN 1992-1-1 cubre fck entre 12 y 90 MPa; "
            f"se recibió fck = {fck} MPa."
        )
    return fck + 8.0


def ecm_tabla_3_1(fcm: float) -> float:
    """Módulo secante del hormigón según la Tabla 3.1.

    ``Ecm = 22·(fcm/10)^0,3`` GPa (EN 1992-1-1, Tabla 3.1).

    Args:
        fcm: Resistencia media a compresión (MPa).

    Returns:
        El módulo secante ``Ecm`` (MPa).
    """
    return 22_000.0 * (fcm / 10.0) ** 0.3


@dataclass(frozen=True, slots=True)
class LeyParabolaRectangulo:
    """Diagrama parábola-rectángulo de cálculo (EN 1992-1-1, 3.1.7(1)).

    Attributes:
        fc: Resistencia de compresión (MPa, valor absoluto) ya resuelta,
            habitualmente ``fcd``.
        eps_c2: Deformación en la tensión máxima (tanto por uno).
        eps_cu2: Deformación última (tanto por uno).
        exponente: Exponente ``n`` de la parábola.
    """

    fc: float
    eps_c2: float
    eps_cu2: float
    exponente: float

    def tension(self, deformacion: float) -> float:
        """Tensión del diagrama parábola-rectángulo.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión (MPa); nula en tracción y tras la deformación última.
        """
        if deformacion > 0.0:
            return 0.0
        compresion = -deformacion
        if compresion > self.eps_cu2:
            return 0.0
        if compresion <= self.eps_c2:
            return -self.fc * (
                1.0 - (1.0 - compresion / self.eps_c2) ** self.exponente
            )
        return -self.fc

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente del diagrama parábola-rectángulo.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La pendiente ``dσ/dε`` (MPa); nula en la meseta y en tracción.
        """
        if deformacion > 0.0:
            return 0.0
        compresion = -deformacion
        if compresion > self.eps_cu2:
            return 0.0
        if compresion < self.eps_c2:
            return (
                self.exponente
                * self.fc
                / self.eps_c2
                * (1.0 - compresion / self.eps_c2) ** (self.exponente - 1.0)
            )
        return 0.0

    @property
    def deformacion_maxima_compresion(self) -> float:
        """Deformación última de compresión (negativa)."""
        return -self.eps_cu2

    @property
    def deformacion_maxima_traccion(self) -> float:
        """El hormigón fisurado no colabora a tracción."""
        return 0.0


@dataclass(frozen=True, slots=True)
class LeyBilineal:
    """Diagrama bilineal de cálculo (EN 1992-1-1, 3.1.7(2)).

    Attributes:
        fc: Resistencia de compresión (MPa, valor absoluto) ya resuelta,
            habitualmente ``fcd``.
        eps_c3: Deformación en la tensión máxima (tanto por uno).
        eps_cu3: Deformación última (tanto por uno).
    """

    fc: float
    eps_c3: float
    eps_cu3: float

    def tension(self, deformacion: float) -> float:
        """Tensión del diagrama bilineal.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión (MPa); nula en tracción y tras la deformación última.
        """
        if deformacion > 0.0:
            return 0.0
        compresion = -deformacion
        if compresion > self.eps_cu3:
            return 0.0
        return -self.fc * min(compresion / self.eps_c3, 1.0)

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente del diagrama bilineal.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            El módulo secante ``fc/εc3`` en la rama lineal y cero en la meseta
            o en tracción (MPa).
        """
        if deformacion > 0.0:
            return 0.0
        compresion = -deformacion
        if compresion >= self.eps_c3 or compresion > self.eps_cu3:
            return 0.0
        return self.fc / self.eps_c3

    @property
    def deformacion_maxima_compresion(self) -> float:
        """Deformación última de compresión (negativa)."""
        return -self.eps_cu3

    @property
    def deformacion_maxima_traccion(self) -> float:
        """El hormigón fisurado no colabora a tracción."""
        return 0.0


@dataclass(frozen=True, slots=True)
class LeyNoLinealGeneral:
    """Diagrama general no lineal (EN 1992-1-1, 3.1.5, ecuación 3.14).

    ``σ = -fc·(k·η - η²) / (1 + (k - 2)·η)``, con ``η = |ε|/εc1`` y
    ``k = 1,05·Ecm·εc1/fc``. Incluye la rama descendente hasta ``εcu1``.

    Attributes:
        fc: Resistencia de compresión (MPa, valor absoluto) ya resuelta,
            habitualmente ``fcm``.
        ecm: Módulo de deformación secante (MPa).
        eps_c1: Deformación en la tensión máxima (tanto por uno).
        eps_cu1: Deformación última (tanto por uno).
    """

    fc: float
    ecm: float
    eps_c1: float
    eps_cu1: float

    @property
    def k(self) -> float:
        """Parámetro de forma ``k = 1,05·Ecm·εc1/fc``."""
        return 1.05 * self.ecm * self.eps_c1 / self.fc

    def tension(self, deformacion: float) -> float:
        """Tensión del diagrama general no lineal.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión (MPa); nula en tracción y tras la deformación última.
        """
        if deformacion > 0.0:
            return 0.0
        compresion = -deformacion
        if compresion > self.eps_cu1:
            return 0.0
        eta = compresion / self.eps_c1
        k = self.k
        return -self.fc * (k * eta - eta**2) / (1.0 + (k - 2.0) * eta)

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente del diagrama general no lineal.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La pendiente ``dσ/dε`` (MPa); negativa en la rama descendente.
        """
        if deformacion > 0.0:
            return 0.0
        compresion = -deformacion
        if compresion > self.eps_cu1:
            return 0.0
        eta = compresion / self.eps_c1
        k = self.k
        pendiente = (k - 2.0 * eta - (k - 2.0) * eta**2) / (
            1.0 + (k - 2.0) * eta
        ) ** 2
        return self.fc / self.eps_c1 * pendiente

    @property
    def deformacion_maxima_compresion(self) -> float:
        """Deformación última de compresión (negativa)."""
        return -self.eps_cu1

    @property
    def deformacion_maxima_traccion(self) -> float:
        """El hormigón fisurado no colabora a tracción."""
        return 0.0


def ley_hormigon_lineal(
    hormigon: Hormigon, coeficiente_fluencia: float = 0.0
) -> LeyElastica:
    """Ley elástica con el módulo secante del hormigón.

    Args:
        hormigon: Hormigón del que se toma el módulo secante ``Ecm``.
        coeficiente_fluencia: Coeficiente de fluencia ``φ(t, t0)`` para el
            módulo efectivo ``Ec,ef = Ecm/(1 + φ)`` (EN 1992-1-1, 7.2(3)).
            Por defecto 0 (análisis instantáneo).

    Returns:
        La ley elástica lineal con el módulo efectivo.
    """
    return LeyElastica(
        modulo_elasticidad=hormigon.ecm / (1.0 + coeficiente_fluencia)
    )


def ley_hormigon_parabola(
    hormigon: Hormigon, gamma_c: float
) -> LeyParabolaRectangulo:
    """Ley parábola-rectángulo de cálculo.

    Args:
        hormigon: Hormigón del modelo.
        gamma_c: Coeficiente parcial de seguridad del hormigón.

    Returns:
        La ley con ``fc = fck/γc`` y las deformaciones de la Tabla 3.1.
    """
    deformaciones = deformaciones_tabla_3_1(hormigon.fck, hormigon.fcm)
    return LeyParabolaRectangulo(
        fc=hormigon.fck / gamma_c,
        eps_c2=deformaciones.eps_c2,
        eps_cu2=deformaciones.eps_cu2,
        exponente=deformaciones.exponente,
    )


def ley_hormigon_bilineal(hormigon: Hormigon, gamma_c: float) -> LeyBilineal:
    """Ley bilineal de cálculo.

    Args:
        hormigon: Hormigón del modelo.
        gamma_c: Coeficiente parcial de seguridad del hormigón.

    Returns:
        La ley con ``fc = fck/γc`` y las deformaciones de la Tabla 3.1.
    """
    deformaciones = deformaciones_tabla_3_1(hormigon.fck, hormigon.fcm)
    return LeyBilineal(
        fc=hormigon.fck / gamma_c,
        eps_c3=deformaciones.eps_c3,
        eps_cu3=deformaciones.eps_cu3,
    )


def ley_hormigon_no_lineal(hormigon: Hormigon) -> LeyNoLinealGeneral:
    """Ley general no lineal con valores medios.

    Args:
        hormigon: Hormigón del modelo, del que se toman ``fcm`` y ``Ecm``.

    Returns:
        La ley general con las deformaciones de la Tabla 3.1.
    """
    deformaciones = deformaciones_tabla_3_1(hormigon.fck, hormigon.fcm)
    return LeyNoLinealGeneral(
        fc=hormigon.fcm,
        ecm=hormigon.ecm,
        eps_c1=deformaciones.eps_c1,
        eps_cu1=deformaciones.eps_cu1,
    )


@dataclass(frozen=True, slots=True)
class LeyBilinealEndurecida:
    """Diagrama bilineal con endurecimiento del acero pasivo.

    Corresponde a la rama inclinada de EN 1992-1-1, 3.2.7(1), figura 3.7a
    (adoptada por el Código Estructural). La rama elástica llega hasta
    ``fyd`` en ``εyd``; a partir de ahí la tensión crece linealmente hasta
    ``ftd`` en ``εud`` y se anula para deformaciones mayores.

    Attributes:
        modulo_elasticidad: Módulo de elasticidad ``Es`` (MPa).
        limite_elastico: Límite elástico de cálculo ``fyd`` (MPa, valor
            absoluto).
        resistencia_ultima: Resistencia de cálculo a rotura ``ftd`` (MPa,
            valor absoluto).
        deformacion_ultima: Deformación última de cálculo ``εud`` (tanto por
            uno, valor absoluto).
    """

    modulo_elasticidad: float
    limite_elastico: float
    resistencia_ultima: float
    deformacion_ultima: float

    @property
    def deformacion_fluencia(self) -> float:
        """Deformación de fluencia ``εyd = fyd/Es`` (positiva)."""
        return self.limite_elastico / self.modulo_elasticidad

    def tension(self, deformacion: float) -> float:
        """Tensión del diagrama bilineal con endurecimiento.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            La tensión (MPa), positiva en tracción y negativa en compresión;
            nula tras la deformación última.
        """
        deformacion_absoluta = abs(deformacion)
        if deformacion_absoluta > self.deformacion_ultima:
            return 0.0
        if deformacion_absoluta <= self.deformacion_fluencia:
            return self.modulo_elasticidad * deformacion

        signo = 1.0 if deformacion > 0.0 else -1.0
        exceso = deformacion_absoluta - self.deformacion_fluencia
        pendiente_endurecimiento = (
            self.resistencia_ultima - self.limite_elastico
        ) / (self.deformacion_ultima - self.deformacion_fluencia)
        return signo * (
            self.limite_elastico + pendiente_endurecimiento * exceso
        )

    def modulo_tangente(self, deformacion: float) -> float:
        """Pendiente del diagrama bilineal con endurecimiento.

        Args:
            deformacion: Deformación longitudinal (tanto por uno).

        Returns:
            El módulo ``Es`` en la rama elástica, la pendiente de
            endurecimiento en la rama inclinada (MPa) y cero tras la
            deformación última.
        """
        deformacion_absoluta = abs(deformacion)
        if deformacion_absoluta > self.deformacion_ultima:
            return 0.0
        if deformacion_absoluta <= self.deformacion_fluencia:
            return self.modulo_elasticidad
        return (self.resistencia_ultima - self.limite_elastico) / (
            self.deformacion_ultima - self.deformacion_fluencia
        )

    @property
    def deformacion_maxima_compresion(self) -> float:
        """Deformación última de compresión (negativa)."""
        return -self.deformacion_ultima

    @property
    def deformacion_maxima_traccion(self) -> float:
        """Deformación última de tracción (positiva)."""
        return self.deformacion_ultima


def _deformacion_ultima_de_diseno(
    acero: AceroArmadura, gamma_s: float
) -> float:
    """Deformación última de cálculo ``εud = 0,9·εuk``.

    Args:
        acero: Acero pasivo con su alargamiento característico ``εuk``.
        gamma_s: Coeficiente parcial de seguridad del acero.

    Returns:
        La deformación última de cálculo (tanto por uno).

    Raises:
        CasoFueraDeAlcance: Si ``gamma_s`` no es positivo o si la deformación
            última no supera la de fluencia (el acero no tendría rama
            plástica).
    """
    if gamma_s <= 0.0:
        raise CasoFueraDeAlcance(
            "El coeficiente parcial del acero gamma_s debe ser positivo; "
            f"se recibió {gamma_s}."
        )

    deformacion_ultima = _FACTOR_DEFORMACION_ULTIMA * acero.eps_uk
    deformacion_fluencia = (acero.fyk / gamma_s) / acero.es
    if deformacion_ultima <= deformacion_fluencia:
        raise CasoFueraDeAlcance(
            "El acero no tiene rama plástica con los parámetros dados: "
            f"εud = {deformacion_ultima} no supera εyd = "
            f"{deformacion_fluencia} (eps_uk = {acero.eps_uk}, "
            f"gamma_s = {gamma_s})."
        )
    return deformacion_ultima


def ley_acero_pasivo_bilineal(
    acero: AceroArmadura, gamma_s: float
) -> LeyElastoplastica:
    """Ley de cálculo con rama superior horizontal (3.2.7(2), figura 3.7b).

    Args:
        acero: Acero pasivo del modelo.
        gamma_s: Coeficiente parcial de seguridad del acero.

    Returns:
        La ley elastoplástica perfecta con ``fyd = fyk/γs`` y
        ``εud = 0,9·εuk``.
    """
    deformacion_ultima = _deformacion_ultima_de_diseno(acero, gamma_s)
    return LeyElastoplastica(
        modulo_elasticidad=acero.es,
        limite_elastico=acero.fyk / gamma_s,
        deformacion_ultima=deformacion_ultima,
    )


def ley_acero_pasivo_endurecida(
    acero: AceroArmadura, gamma_s: float
) -> LeyBilinealEndurecida:
    """Ley de cálculo con rama inclinada (3.2.7(1), figura 3.7a).

    Args:
        acero: Acero pasivo del modelo.
        gamma_s: Coeficiente parcial de seguridad del acero.

    Returns:
        La ley bilineal con ``fyd = fyk/γs``, ``ftd = ftk/γs`` y
        ``εud = 0,9·εuk``.
    """
    deformacion_ultima = _deformacion_ultima_de_diseno(acero, gamma_s)
    return LeyBilinealEndurecida(
        modulo_elasticidad=acero.es,
        limite_elastico=acero.fyk / gamma_s,
        resistencia_ultima=acero.ftk / gamma_s,
        deformacion_ultima=deformacion_ultima,
    )
