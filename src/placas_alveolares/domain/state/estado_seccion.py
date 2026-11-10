"""Estado deformacional de una sección en una fase concreta."""

from __future__ import annotations

from dataclasses import dataclass, replace

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.model.seccion import (
    ComponenteId,
    CondicionAdherencia,
)
from placas_alveolares.domain.state.plano_deformaciones import (
    PLANO_NULO,
    PlanoDeformaciones,
)
from placas_alveolares.domain.state.resultantes import ResultantesSeccion


@dataclass(frozen=True, slots=True)
class EstadoComponenteFase:
    """Estado de un componente activo dentro de una fase.

    Guarda lo que el componente aporta al cálculo además de su geometría y
    material: desde qué plano empezó a trabajar y qué deformación propia
    lleva impuesta. La deformación que ve su ley constitutiva se obtiene con
    :meth:`deformacion_constitutiva`.

    Attributes:
        componente_id: Identificador del componente de la sección.
        plano_referencia: Plano común en el que el componente quedó libre de
            tensión al activarse o adherirse. Se fija al incorporarlo y al
            pasar de enfundado a adherido.
        deformacion_impuesta: Deformación propia del componente, como el
            pretensado; se suma a la deformación común.
        adherencia: Condición de adherencia vigente en esta fase. Si no está
            adherido, el componente no se integra en el equilibrio.
    """

    componente_id: ComponenteId
    plano_referencia: PlanoDeformaciones
    deformacion_impuesta: PlanoDeformaciones = PLANO_NULO
    adherencia: CondicionAdherencia = CondicionAdherencia.ADHERIDO

    def deformacion_constitutiva(
        self,
        plano_comun: PlanoDeformaciones,
    ) -> PlanoDeformaciones:
        """Deformación que se evalúa en la ley constitutiva.

        Args:
            plano_comun: Plano cinemático vigente de la sección.

        Returns:
            ``plano_comun − plano_referencia + deformacion_impuesta``.
        """
        return (
            plano_comun - self.plano_referencia + self.deformacion_impuesta
        )


@dataclass(frozen=True, slots=True)
class ResumenEquilibrio:
    """Resumen numérico de una resolución de equilibrio.

    Attributes:
        resultantes: Resultantes internas en el plano resuelto.
        iteraciones: Número de iteraciones realizadas por el solver.
        norma_residuo: Norma final del residuo normalizado.
        norma_residuo_inicial: Norma inicial del residuo normalizado.
    """

    resultantes: ResultantesSeccion
    iteraciones: int
    norma_residuo: float
    norma_residuo_inicial: float


@dataclass(frozen=True, slots=True)
class EstadoSeccionFase:
    """Estado completo de una sección al final de una fase.

    Reúne el plano cinemático común, el estado de cada componente activado y,
    si la fase resolvió equilibrio, el resumen numérico del solver. Es
    inmutable: cada fase produce un estado nuevo que se encadena al anterior
    y se conserva en :class:`HistorialSeccion`.

    Attributes:
        fase: Índice de la fase que representa el estado.
        plano_comun: Plano de deformaciones cinemático de la sección,
            compartido por los componentes adheridos.
        componentes: Estados de los componentes ya activados, en el orden en
            que se activaron.
        equilibrio: Resumen del equilibrio o ``None`` si la fase solo
            actualiza el estado (p. ej. tesado o pérdidas).

    Raises:
        ErrorValidacion: Si hay identificadores de componente repetidos.
    """

    fase: int
    plano_comun: PlanoDeformaciones
    componentes: tuple[EstadoComponenteFase, ...]
    equilibrio: ResumenEquilibrio | None = None

    def __post_init__(self) -> None:
        identificadores = [
            componente.componente_id for componente in self.componentes
        ]
        if len(set(identificadores)) != len(identificadores):
            raise ErrorValidacion(
                "El estado de la sección no puede contener componentes "
                "repetidos."
            )

    def componente(
        self,
        componente_id: ComponenteId,
    ) -> EstadoComponenteFase | None:
        """Busca el estado de un componente por su identificador."""
        for componente in self.componentes:
            if componente.componente_id == componente_id:
                return componente
        return None

    def componente_requerido(
        self,
        componente_id: ComponenteId,
    ) -> EstadoComponenteFase:
        """Devuelve un componente activo o lanza un error.

        Raises:
            ErrorValidacion: Si el componente no está activo en este estado.
        """
        componente = self.componente(componente_id)
        if componente is None:
            raise ErrorValidacion(
                f"El componente '{componente_id}' no está activo en la fase "
                f"{self.fase}."
            )
        return componente

    def con_componente(
        self,
        actualizado: EstadoComponenteFase,
    ) -> EstadoSeccionFase:
        """Devuelve un estado nuevo con un componente reemplazado.

        Raises:
            ErrorValidacion: Si el componente no pertenece al estado.
        """
        encontrado = False
        componentes: list[EstadoComponenteFase] = []
        for componente in self.componentes:
            if componente.componente_id == actualizado.componente_id:
                componentes.append(actualizado)
                encontrado = True
            else:
                componentes.append(componente)
        if not encontrado:
            raise ErrorValidacion(
                f"El componente '{actualizado.componente_id}' no pertenece "
                f"al estado de la fase {self.fase}."
            )
        return replace(self, componentes=tuple(componentes))

    def con_deformacion_impuesta(
        self,
        componente_id: ComponenteId,
        deformacion: PlanoDeformaciones,
    ) -> EstadoSeccionFase:
        """Actualiza la deformación impuesta de un componente."""
        componente = self.componente_requerido(componente_id)
        return self.con_componente(
            replace(componente, deformacion_impuesta=deformacion)
        )

    def con_adherencia_y_referencia(
        self,
        componente_id: ComponenteId,
        adherencia: CondicionAdherencia,
        plano_referencia: PlanoDeformaciones,
    ) -> EstadoSeccionFase:
        """Actualiza adherencia y plano de referencia de un componente."""
        componente = self.componente_requerido(componente_id)
        return self.con_componente(
            replace(
                componente,
                adherencia=adherencia,
                plano_referencia=plano_referencia,
            )
        )

    def con_plano_y_resumen(
        self,
        plano_comun: PlanoDeformaciones,
        equilibrio: ResumenEquilibrio,
    ) -> EstadoSeccionFase:
        """Devuelve un estado nuevo con el plano y el resumen resueltos."""
        return replace(
            self,
            plano_comun=plano_comun,
            equilibrio=equilibrio,
        )


def estado_inicial(fase: int) -> EstadoSeccionFase:
    """Crea el estado vacío anterior a la primera fase.

    Args:
        fase: Índice de la primera fase que se va a calcular; solo etiqueta
            el estado de partida.

    Returns:
        Un estado sin componentes activos y con plano común nulo.
    """
    return EstadoSeccionFase(
        fase=fase,
        plano_comun=PLANO_NULO,
        componentes=(),
        equilibrio=None,
    )
