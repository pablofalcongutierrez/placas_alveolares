"""Operaciones concretas sobre el estado seccional."""

from __future__ import annotations

import math
from dataclasses import dataclass

from placas_alveolares.domain.errores import ErrorValidacion
from placas_alveolares.domain.model.geometria import area_geometria
from placas_alveolares.domain.model.materiales import AceroPretensado
from placas_alveolares.domain.model.operaciones import (
    PerdidaPorTension,
    PerdidaPretensado,
    PretensadoInicial,
    PretensadoPorFuerza,
    PretensadoPorPlano,
)
from placas_alveolares.domain.model.seccion import (
    ComponenteId,
    ComponenteSeccion,
    CondicionAdherencia,
    Seccion,
)
from placas_alveolares.domain.state.estado_seccion import EstadoSeccionFase
from placas_alveolares.domain.state.plano_deformaciones import (
    PlanoDeformaciones,
)


def _validar_plano(plano: PlanoDeformaciones) -> None:
    """Valida que un plano contenga solo valores finitos."""
    if not all(
        math.isfinite(valor)
        for valor in (plano.eps0, plano.kappa_y, plano.kappa_z)
    ):
        raise ErrorValidacion(
            "El plano de deformaciones debe contener valores finitos."
        )


def _plano_axial(deformacion: float) -> PlanoDeformaciones:
    """Construye un plano de deformación axial uniforme."""
    if not math.isfinite(deformacion):
        raise ErrorValidacion(
            f"La deformación debe ser finita; se recibió {deformacion}."
        )
    return PlanoDeformaciones(
        eps0=deformacion,
        kappa_y=0.0,
        kappa_z=0.0,
    )


def _componente_pretensado(
    seccion: Seccion,
    componente_id: ComponenteId,
) -> ComponenteSeccion:
    """Obtiene un componente y comprueba que sea acero de pretensado."""
    componente = seccion.componente_por_id(componente_id)
    if not isinstance(componente.material, AceroPretensado):
        raise ErrorValidacion(
            f"El componente '{componente_id}' no es acero de pretensado."
        )
    return componente


@dataclass(frozen=True, slots=True)
class AsignarDeformacionImpuesta:
    """Asigna un plano de deformación impuesta a un componente.

    Attributes:
        componente_id: Componente sobre el que se actúa.
        deformacion: Plano impuesto que sustituye al anterior.
    """

    componente_id: ComponenteId
    deformacion: PlanoDeformaciones

    def aplicar(
        self,
        estado: EstadoSeccionFase,
        seccion: Seccion,
    ) -> EstadoSeccionFase:
        """Sustituye la deformación impuesta del componente."""
        _validar_plano(self.deformacion)
        estado.componente_requerido(self.componente_id)
        return estado.con_deformacion_impuesta(
            self.componente_id,
            self.deformacion,
        )


@dataclass(frozen=True, slots=True)
class AsignarPretensado:
    """Asigna el pretensado inicial de un tendón.

    Attributes:
        componente_id: Componente de acero de pretensado.
        pretensado: Fuerza, tensión o plano de deformaciones inicial.
    """

    componente_id: ComponenteId
    pretensado: PretensadoInicial

    def aplicar(
        self,
        estado: EstadoSeccionFase,
        seccion: Seccion,
    ) -> EstadoSeccionFase:
        """Convierte el pretensado a deformación y lo asigna al tendón.

        Raises:
            ErrorValidacion: Si el componente no es de pretensado, no está
                activo o su área no permite convertir una fuerza.
        """
        componente = _componente_pretensado(seccion, self.componente_id)
        estado.componente_requerido(self.componente_id)

        if isinstance(self.pretensado, PretensadoPorPlano):
            plano = self.pretensado.plano
            _validar_plano(plano)
        else:
            material = componente.material
            assert isinstance(material, AceroPretensado)
            if isinstance(self.pretensado, PretensadoPorFuerza):
                area = area_geometria(componente.geometria)
                if area <= 0.0:
                    raise ErrorValidacion(
                        f"El componente '{self.componente_id}' no tiene área "
                        "positiva para convertir la fuerza de tesado."
                    )
                tension = self.pretensado.fuerza / area
            else:
                tension = self.pretensado.tension
            plano = _plano_axial(tension / material.ep)

        return estado.con_deformacion_impuesta(self.componente_id, plano)


@dataclass(frozen=True, slots=True)
class AplicarPerdidaPretensado:
    """Aplica una pérdida de pretensado ya calculada.

    Attributes:
        componente_id: Componente de acero de pretensado.
        perdida: Pérdida de tensión o de deformación axial.
    """

    componente_id: ComponenteId
    perdida: PerdidaPretensado

    def aplicar(
        self,
        estado: EstadoSeccionFase,
        seccion: Seccion,
    ) -> EstadoSeccionFase:
        """Reduce la deformación impuesta sin invertir el pretensado.

        Raises:
            ErrorValidacion: Si la pérdida supera el pretensado vigente.
        """
        componente = _componente_pretensado(seccion, self.componente_id)
        material = componente.material
        assert isinstance(material, AceroPretensado)
        estado_componente = estado.componente_requerido(self.componente_id)

        if isinstance(self.perdida, PerdidaPorTension):
            perdida_deformacion = self.perdida.tension / material.ep
        else:
            perdida_deformacion = self.perdida.deformacion

        actual = estado_componente.deformacion_impuesta
        if perdida_deformacion > actual.eps0:
            raise ErrorValidacion(
                f"La pérdida de deformación {perdida_deformacion} supera el "
                f"pretensado vigente {actual.eps0} del componente "
                f"'{self.componente_id}'."
            )
        plano = PlanoDeformaciones(
            eps0=actual.eps0 - perdida_deformacion,
            kappa_y=actual.kappa_y,
            kappa_z=actual.kappa_z,
        )
        return estado.con_deformacion_impuesta(self.componente_id, plano)


@dataclass(frozen=True, slots=True)
class AdherirComponente:
    """Activa la adherencia de un tendón previamente enfundado.

    Attributes:
        componente_id: Componente que pasa a estar adherido.
    """

    componente_id: ComponenteId

    def aplicar(
        self,
        estado: EstadoSeccionFase,
        seccion: Seccion,
    ) -> EstadoSeccionFase:
        """Fija la referencia al plano común vigente y adhiere el componente.

        Raises:
            ErrorValidacion: Si el componente ya está adherido o no es de
                pretensado.
        """
        _componente_pretensado(seccion, self.componente_id)
        estado_componente = estado.componente_requerido(self.componente_id)
        if estado_componente.adherencia is CondicionAdherencia.ADHERIDO:
            raise ErrorValidacion(
                f"El componente '{self.componente_id}' ya está adherido."
            )
        return estado.con_adherencia_y_referencia(
            self.componente_id,
            CondicionAdherencia.ADHERIDO,
            estado.plano_comun,
        )
