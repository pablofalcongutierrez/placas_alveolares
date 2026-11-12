"""Pruebas del proveedor de leyes de cálculo ELU del Eurocódigo 2."""

from __future__ import annotations

import pytest

from placas_alveolares.domain.mechanics.generic_laws import LeyElastoplastica
from placas_alveolares.domain.mechanics.preparacion_componentes import (
    ProveedorLeyes,
)
from placas_alveolares.domain.model.fases import Fase
from placas_alveolares.domain.model.geometria import rectangulo
from placas_alveolares.domain.model.materiales import (
    AceroArmadura,
    AceroPretensado,
    Hormigon,
)
from placas_alveolares.domain.model.seccion import ComponenteSeccion
from placas_alveolares.domain.model.tiempo import Tiempo
from placas_alveolares.domain.value_objects.coeficientes_parciales import (
    CoeficientesParciales,
)
from placas_alveolares.norms.errores import CasoFueraDeAlcance
from placas_alveolares.norms.eurocode.laws import (
    LeyBilineal,
    LeyBilinealEndurecida,
    LeyParabolaRectangulo,
)
from placas_alveolares.norms.eurocode.proveedor_leyes import (
    ConfiguracionLeyesELUEurocodigo,
    DiagramaAceroPasivoELU,
    DiagramaHormigonELU,
    ProveedorLeyesELUEurocodigo,
)

_HORMIGON = Hormigon(fck=30.0, fcm=38.0, ecm=33_000.0)
_ACERO = AceroArmadura(
    fyk=500.0,
    ftk=550.0,
    es=200_000.0,
    eps_uk=0.075,
)
_PRETENSADO = AceroPretensado(fpk=1_860.0, ep=195_000.0)
_FASE = Fase(
    indice=0,
    tiempo_inicio=Tiempo(0.0),
    tiempo_fin=Tiempo(0.0),
)


def _componente(
    material: Hormigon | AceroArmadura | AceroPretensado,
) -> ComponenteSeccion:
    """Construye un componente con una geometría válida y el material dado."""
    return ComponenteSeccion(
        id="componente",
        geometria=rectangulo(100.0, 200.0),
        material=material,
    )


def test_configuracion_por_defecto_usa_los_diagramas_habituales() -> None:
    """La configuración ELU parte de parábola-rectángulo y rama horizontal."""
    configuracion = ConfiguracionLeyesELUEurocodigo()

    assert configuracion.coeficientes.gamma_c == pytest.approx(1.5)
    assert configuracion.coeficientes.gamma_s == pytest.approx(1.15)
    assert (
        configuracion.diagrama_hormigon
        is DiagramaHormigonELU.PARABOLA_RECTANGULO
    )
    assert (
        configuracion.diagrama_acero_pasivo
        is DiagramaAceroPasivoELU.BILINEAL
    )


def test_hormigon_usa_parabola_rectangulo_por_defecto() -> None:
    """La ley por defecto es la parábola-rectángulo con fck/gamma_c."""
    proveedor = ProveedorLeyesELUEurocodigo()

    ley = proveedor.ley_para(_componente(_HORMIGON), _FASE)

    assert isinstance(ley, LeyParabolaRectangulo)
    assert ley.fc == pytest.approx(20.0)
    assert ley.tension(-0.002) == pytest.approx(-20.0)


def test_hormigon_puede_usar_el_diagrama_bilineal() -> None:
    """La configuración selecciona el diagrama bilineal cuando se solicita."""
    configuracion = ConfiguracionLeyesELUEurocodigo(
        diagrama_hormigon=DiagramaHormigonELU.BILINEAL
    )
    proveedor = ProveedorLeyesELUEurocodigo(configuracion)

    ley = proveedor.ley_para(_componente(_HORMIGON), _FASE)

    assert isinstance(ley, LeyBilineal)
    assert ley.fc == pytest.approx(20.0)
    assert ley.tension(-0.00175) == pytest.approx(-20.0)


def test_hormigon_usa_los_coeficientes_configurados() -> None:
    """Los coeficientes de la configuración se propagan a la ley."""
    configuracion = ConfiguracionLeyesELUEurocodigo(
        coeficientes=CoeficientesParciales(gamma_c=1.3, gamma_s=1.0)
    )
    proveedor = ProveedorLeyesELUEurocodigo(configuracion)

    ley = proveedor.ley_para(_componente(_HORMIGON), _FASE)

    assert isinstance(ley, LeyParabolaRectangulo)
    assert ley.fc == pytest.approx(30.0 / 1.3)


def test_acero_pasivo_usa_rama_horizontal_por_defecto() -> None:
    """La ley por defecto del acero pasivo es elastoplástica perfecta."""
    proveedor = ProveedorLeyesELUEurocodigo()

    ley = proveedor.ley_para(_componente(_ACERO), _FASE)

    assert isinstance(ley, LeyElastoplastica)
    assert ley.limite_elastico == pytest.approx(500.0 / 1.15)
    assert ley.deformacion_ultima == pytest.approx(0.9 * 0.075)


def test_acero_pasivo_puede_usar_rama_endurecida() -> None:
    """La configuración selecciona la rama inclinada cuando se solicita."""
    configuracion = ConfiguracionLeyesELUEurocodigo(
        diagrama_acero_pasivo=DiagramaAceroPasivoELU.ENDURECIDA,
        coeficientes=CoeficientesParciales(gamma_c=1.5, gamma_s=1.0),
    )
    proveedor = ProveedorLeyesELUEurocodigo(configuracion)

    ley = proveedor.ley_para(_componente(_ACERO), _FASE)

    assert isinstance(ley, LeyBilinealEndurecida)
    assert ley.limite_elastico == pytest.approx(500.0)
    assert ley.resistencia_ultima == pytest.approx(550.0)
    assert ley.tension(0.9 * 0.075) == pytest.approx(550.0)


def test_pretensado_queda_fuera_del_alcance_del_elu() -> None:
    """No se ofrece una ley ELU incompleta para el acero de pretensado."""
    proveedor = ProveedorLeyesELUEurocodigo()

    with pytest.raises(CasoFueraDeAlcance, match="pretensado"):
        proveedor.ley_para(_componente(_PRETENSADO), _FASE)


def test_proveedor_cumple_el_contrato_del_dominio() -> None:
    """El proveedor es intercambiable con cualquier ProveedorLeyes."""
    proveedor: ProveedorLeyes = ProveedorLeyesELUEurocodigo()

    ley = proveedor.ley_para(_componente(_HORMIGON), _FASE)

    assert isinstance(ley, LeyParabolaRectangulo)
