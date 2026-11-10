"""Pruebas de la orquestación de fases y de operaciones personalizadas."""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.domain.mechanics.analisis_fases import analizar_fases
from placas_alveolares.domain.mechanics.laws import LeyTensionDeformacion
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.geometria import rectangulo
from placas_alveolares.domain.model.materiales import Hormigon
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.seccion import ComponenteSeccion, Seccion
from placas_alveolares.domain.model.tiempo import Tiempo
from placas_alveolares.domain.numerics import Newton
from placas_alveolares.domain.state.estado_seccion import EstadoSeccionFase
from placas_alveolares.domain.state.plano_deformaciones import PlanoDeformaciones


@dataclass(frozen=True, slots=True)
class _OperacionPersonalizada:
    """Operación externa que demuestra la extensibilidad del protocolo."""

    def aplicar(
        self,
        estado: EstadoSeccionFase,
        seccion: Seccion,
    ) -> EstadoSeccionFase:
        return estado.con_deformacion_impuesta(
            "hormigon",
            PlanoDeformaciones(
                eps0=2.0e-4,
                kappa_y=0.0,
                kappa_z=0.0,
            ),
        )


@dataclass(frozen=True, slots=True)
class _ProveedorNoUsado:
    """Proveedor que falla si se intenta preparar una ley."""

    def ley_para(
        self,
        componente: ComponenteSeccion,
        fase: Fase,
    ) -> LeyTensionDeformacion:
        raise AssertionError("No se esperaba preparar leyes.")


def test_operacion_personalizada_se_ejecuta_sin_cambiar_el_bucle() -> None:
    """Cualquier objeto que cumpla OperacionFase se aplica en orden."""
    hormigon = ComponenteSeccion(
        id="hormigon",
        geometria=rectangulo(300.0, 500.0),
        material=Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0),
    )
    modelo = ModeloEstructural(
        seccion=Seccion(componentes=(hormigon,)),
        fases=(
            Fase(
                indice=0,
                tiempo_inicio=Tiempo(0.0),
                tiempo_fin=Tiempo(0.0),
                resolver_equilibrio=False,
                operaciones=(_OperacionPersonalizada(),),
            ),
        ),
    )

    historial = analizar_fases(
        modelo,
        _ProveedorNoUsado(),
        Newton(),
    )

    estado = historial.estado(0)
    assert estado.equilibrio is None
    assert estado.componente_requerido(
        "hormigon"
    ).deformacion_impuesta.eps0 == 2.0e-4
