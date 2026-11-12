"""Construcción del modelo portable de sección, deformaciones y tensiones.

El caso de uso no resuelve equilibrio: proyecta un :class:`HistorialSeccion`
ya calculado al contrato de :mod:`visualizacion_tensiones`. Para ello recupera
la geometría efectiva, la malla y la ley de cada fase con los mismos motores del
análisis, evalúa las tensiones con el plano constitutivo de cada componente y
expresa toda la geometría en el sistema alineado con la línea neutra.
"""

from __future__ import annotations

from dataclasses import dataclass

from placas_alveolares.application.dtos.visualizacion_tensiones import (
    VERSION_FORMATO,
    AdherenciaVista,
    ComponenteVista,
    ContornoVista,
    EvolucionAlineadaVista,
    FaseAlineadaVista,
    GeometriaVista,
    LimitesFaseVista,
    MuestraDeformacionComunVista,
    MuestraPerfilVista,
    PerfilComponenteVista,
    PuntoVista,
    RangoVista,
    TipoMaterialVista,
    TramoPerfilVista,
)
from placas_alveolares.application.errores import VisualizacionInvalida
from placas_alveolares.domain.mechanics.alineacion_deformaciones import (
    PuntoAlineado,
    SistemaReferenciaAlineado,
    sistema_referencia_alineado,
)
from placas_alveolares.domain.mechanics.campo_tensiones import evaluar_tension
from placas_alveolares.domain.mechanics.geometria_efectiva import (
    geometria_efectiva,
)
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ComponenteCalculo,
    ProveedorLeyes,
    preparar_componentes,
)
from placas_alveolares.domain.model.fases import (
    Fase,
    componentes_activos,
)
from placas_alveolares.domain.model.geometria import (
    Contorno,
    Punto,
)
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    Hormigon,
    Material,
)
from placas_alveolares.domain.model.modelo import ModeloEstructural
from placas_alveolares.domain.model.seccion import (
    ComponenteSeccion,
    CondicionAdherencia,
)
from placas_alveolares.domain.state.estado_seccion import EstadoSeccionFase
from placas_alveolares.domain.state.historial_seccion import HistorialSeccion

_MUESTRAS_PERFIL_POR_DEFECTO = 161
"""Número de cotas evaluadas en cada perfil vertical."""


@dataclass(frozen=True, slots=True)
class _TrianguloAlineado:
    """Triángulo expresado en coordenadas alineadas."""

    a: PuntoAlineado
    b: PuntoAlineado
    c: PuntoAlineado


def construir_evolucion_alineada(
    modelo: ModeloEstructural,
    historial: HistorialSeccion,
    proveedor_leyes: ProveedorLeyes,
    muestras_perfil: int = _MUESTRAS_PERFIL_POR_DEFECTO,
) -> EvolucionAlineadaVista:
    """Proyecta un historial calculado al contrato de visualización.

    Args:
        modelo: Modelo que originó el historial.
        historial: Estados calculados, uno por fase del modelo.
        proveedor_leyes: Fuente de leyes constitutivas por componente y fase.
        muestras_perfil: Número de cotas evaluadas en cada perfil vertical.
            Debe ser al menos dos.

    Returns:
        La evolución completa alineada, con sección, deformaciones y tensiones
        por fase.

    Raises:
        VisualizacionInvalida: Si se solicitan menos de dos muestras por perfil.
        FaseInvalida: Si el historial no contiene alguna fase del modelo.
    """
    if muestras_perfil < 2:
        raise VisualizacionInvalida(
            "El perfil necesita al menos dos muestras; se recibieron "
            f"{muestras_perfil}."
        )

    fases = tuple(
        _fase_alineada(
            modelo,
            historial,
            fase,
            proveedor_leyes,
            muestras_perfil,
        )
        for fase in modelo.fases
    )
    return EvolucionAlineadaVista(
        version_formato=VERSION_FORMATO,
        unidad_longitud="mm",
        unidad_deformacion="1",
        unidad_tension="MPa",
        fases=fases,
        limites_globales=_limites_globales(fases),
    )


def _fase_alineada(
    modelo: ModeloEstructural,
    historial: HistorialSeccion,
    fase: Fase,
    proveedor_leyes: ProveedorLeyes,
    muestras_perfil: int,
) -> FaseAlineadaVista:
    """Construye la vista alineada de una fase."""
    estado = historial.estado(fase.indice)
    sistema = sistema_referencia_alineado(estado.plano_comun)
    activos = componentes_activos(modelo.seccion, fase.indice)
    preparados = preparar_componentes(
        modelo.seccion,
        fase,
        estado,
        proveedor_leyes,
    )
    componentes = tuple(
        _componente_vista(
            componente,
            modelo,
            activos,
            estado,
            sistema,
            muestras_perfil,
        )
        for componente in preparados
    )

    cotas = tuple(
        punto.v
        for componente in componentes
        for punto in _puntos_geometria(componente.geometria)
    )
    if cotas:
        v_min = min(cotas)
        v_max = max(cotas)
    else:
        v_min = 0.0
        v_max = 0.0

    deformacion_comun = (
        MuestraDeformacionComunVista(
            v=v_min,
            deformacion=sistema.deformacion_comun(v_min),
        ),
        MuestraDeformacionComunVista(
            v=v_max,
            deformacion=sistema.deformacion_comun(v_max),
        ),
    )
    tensiones = tuple(
        muestra.tension
        for componente in componentes
        for tramo in componente.perfil.tramos
        for muestra in tramo.muestras
    )
    deformaciones = tuple(
        muestra.deformacion
        for muestra in deformacion_comun
    ) + tuple(
        muestra.deformacion
        for componente in componentes
        for tramo in componente.perfil.tramos
        for muestra in tramo.muestras
    )

    return FaseAlineadaVista(
        indice=fase.indice,
        nombre=fase.nombre or f"Fase {fase.indice}",
        tiempo_inicio_dias=fase.tiempo_inicio.dias,
        tiempo_fin_dias=fase.tiempo_fin.dias,
        equilibrio_resuelto=estado.equilibrio is not None,
        linea_neutra_definida=sistema.linea_neutra_definida,
        angulo_radianes=sistema.angulo_radianes,
        curvatura=sistema.curvatura,
        deformacion_comun=deformacion_comun,
        componentes=componentes,
        limites=LimitesFaseVista(
            vertical=RangoVista(minimo=v_min, maximo=v_max),
            deformacion=_rango(deformaciones),
            tension=_rango(tensiones),
        ),
    )


def _componente_vista(
    componente: ComponenteCalculo,
    modelo: ModeloEstructural,
    activos: tuple[ComponenteSeccion, ...],
    estado: EstadoSeccionFase,
    sistema: SistemaReferenciaAlineado,
    muestras_perfil: int,
) -> ComponenteVista:
    """Construye la vista alineada de un componente preparado."""
    definicion = modelo.seccion.componente_por_id(componente.componente_id)
    estado_componente = estado.componente_requerido(
        componente.componente_id
    )
    geometria = geometria_efectiva(definicion, activos)
    malla = tuple(
        _triangulo_alineado(triangulo.a, triangulo.b, triangulo.c, sistema)
        for triangulo in componente.malla
    )
    perfil = _perfil_componente(
        componente,
        estado,
        sistema,
        malla,
        muestras_perfil,
    )
    return ComponenteVista(
        componente_id=definicion.id,
        tipo_material=_tipo_material(definicion.material),
        adherencia=_adherencia(estado_componente.adherencia),
        geometria=GeometriaVista(
            exterior=_contorno_vista(geometria.exterior, sistema),
            huecos=tuple(
                _contorno_vista(hueco, sistema)
                for hueco in geometria.huecos
            ),
        ),
        perfil=perfil,
    )


def _contorno_vista(
    contorno: Contorno,
    sistema: SistemaReferenciaAlineado,
) -> ContornoVista:
    """Transforma un contorno de la sección al sistema alineado."""
    return ContornoVista(
        puntos=tuple(
            _punto_vista(sistema.a_alineado(punto))
            for punto in contorno.puntos
        )
    )


def _triangulo_alineado(
    a: Punto,
    b: Punto,
    c: Punto,
    sistema: SistemaReferenciaAlineado,
) -> _TrianguloAlineado:
    """Transforma los vértices de un triángulo al sistema alineado."""
    return _TrianguloAlineado(
        a=sistema.a_alineado(a),
        b=sistema.a_alineado(b),
        c=sistema.a_alineado(c),
    )


def _punto_vista(punto: PuntoAlineado) -> PuntoVista:
    """Convierte un punto del dominio al DTO de visualización."""
    return PuntoVista(u=punto.u, v=punto.v)


def _perfil_componente(
    componente: ComponenteCalculo,
    estado: EstadoSeccionFase,
    sistema: SistemaReferenciaAlineado,
    malla: tuple[_TrianguloAlineado, ...],
    muestras_perfil: int,
) -> PerfilComponenteVista:
    """Muestrea un componente en la vertical que pasa por su centroide."""
    u = _centroide_u(malla)
    cotas = tuple(
        punto.v
        for triangulo in malla
        for punto in (triangulo.a, triangulo.b, triangulo.c)
    )
    if not cotas:
        return PerfilComponenteVista(u=u, tramos=())

    v_min = min(cotas)
    v_max = max(cotas)
    paso = (v_max - v_min) / float(muestras_perfil - 1)
    estado_componente = estado.componente_requerido(
        componente.componente_id
    )
    tramos: list[TramoPerfilVista] = []
    actual: list[MuestraPerfilVista] = []
    for indice in range(muestras_perfil):
        v = v_min + paso * indice
        if _contiene_punto(malla, u, v):
            punto = sistema.a_seccion(PuntoAlineado(u=u, v=v))
            muestra = evaluar_tension(
                componente,
                estado_componente,
                estado.plano_comun,
                punto,
            )
            actual.append(
                MuestraPerfilVista(
                    v=v,
                    deformacion=muestra.deformacion,
                    tension=muestra.tension,
                )
            )
        elif actual:
            tramos.append(TramoPerfilVista(muestras=tuple(actual)))
            actual = []
    if actual:
        tramos.append(TramoPerfilVista(muestras=tuple(actual)))
    return PerfilComponenteVista(u=u, tramos=tuple(tramos))


def _centroide_u(malla: tuple[_TrianguloAlineado, ...]) -> float:
    """Cota tangente del centroide de una malla."""
    area_total = 0.0
    momento = 0.0
    for triangulo in malla:
        area = _area_triangulo(triangulo)
        area_total += area
        momento += area * (
            triangulo.a.u + triangulo.b.u + triangulo.c.u
        ) / 3.0
    if area_total <= 0.0:
        raise VisualizacionInvalida(
            "No se puede situar el perfil de un componente sin área."
        )
    return momento / area_total


def _area_triangulo(triangulo: _TrianguloAlineado) -> float:
    """Área de un triángulo alineado (mm²)."""
    return abs(
        (triangulo.b.u - triangulo.a.u)
        * (triangulo.c.v - triangulo.a.v)
        - (triangulo.c.u - triangulo.a.u)
        * (triangulo.b.v - triangulo.a.v)
    ) / 2.0


def _contiene_punto(
    malla: tuple[_TrianguloAlineado, ...],
    u: float,
    v: float,
) -> bool:
    """Indica si una cota de perfil atraviesa la malla del componente."""
    return any(
        _punto_en_triangulo(u, v, triangulo)
        for triangulo in malla
    )


def _punto_en_triangulo(
    u: float,
    v: float,
    triangulo: _TrianguloAlineado,
) -> bool:
    """Comprueba la pertenencia de un punto a un triángulo, con tolerancia."""
    lados = (
        _lado(triangulo.a, triangulo.b, u, v),
        _lado(triangulo.b, triangulo.c, u, v),
        _lado(triangulo.c, triangulo.a, u, v),
    )
    tolerancia = 1.0e-9
    return all(lado >= -tolerancia for lado in lados) or all(
        lado <= tolerancia for lado in lados
    )


def _lado(
    inicio: PuntoAlineado,
    fin: PuntoAlineado,
    u: float,
    v: float,
) -> float:
    """Producto vectorial que sitúa un punto respecto a una arista."""
    return (fin.u - inicio.u) * (v - inicio.v) - (
        fin.v - inicio.v
    ) * (u - inicio.u)


def _puntos_geometria(geometria: GeometriaVista) -> tuple[PuntoVista, ...]:
    """Puntos de todos los contornos de una geometría."""
    return geometria.exterior.puntos + tuple(
        punto
        for hueco in geometria.huecos
        for punto in hueco.puntos
    )


def _tipo_material(material: Material) -> TipoMaterialVista:
    """Clasifica el material para el contrato de presentación."""
    if isinstance(material, Hormigon):
        return TipoMaterialVista.HORMIGON
    if isinstance(material, AceroArmadura):
        return TipoMaterialVista.ACERO_ARMADURA
    return TipoMaterialVista.ACERO_PRETENSADO


def _adherencia(condicion: CondicionAdherencia) -> AdherenciaVista:
    """Traduce la condición de adherencia al contrato de presentación."""
    if condicion is CondicionAdherencia.ADHERIDO:
        return AdherenciaVista.ADHERIDO
    return AdherenciaVista.ENFUNDADO


def _rango(valores: tuple[float, ...]) -> RangoVista:
    """Construye un rango a partir de valores no vacíos."""
    if not valores:
        return RangoVista(minimo=0.0, maximo=0.0)
    return RangoVista(minimo=min(valores), maximo=max(valores))


def _limites_globales(
    fases: tuple[FaseAlineadaVista, ...],
) -> LimitesFaseVista:
    """Rangos que engloban todas las fases del historial."""
    return LimitesFaseVista(
        vertical=RangoVista(
            minimo=min(fase.limites.vertical.minimo for fase in fases),
            maximo=max(fase.limites.vertical.maximo for fase in fases),
        ),
        deformacion=RangoVista(
            minimo=min(fase.limites.deformacion.minimo for fase in fases),
            maximo=max(fase.limites.deformacion.maximo for fase in fases),
        ),
        tension=RangoVista(
            minimo=min(fase.limites.tension.minimo for fase in fases),
            maximo=max(fase.limites.tension.maximo for fase in fases),
        ),
    )
