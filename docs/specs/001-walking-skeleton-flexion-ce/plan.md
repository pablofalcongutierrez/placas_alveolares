# Plan técnico — Milestone 001

> Fundamentos teóricos y convenciones: [`bases_calculo.md`](bases_calculo.md).
> Requisitos y criterios de aceptación: [`spec.md`](spec.md).

## Flujo end-to-end

```
StructuralModel ──preparador──► FlexureInput ──┐
                                               ├─► FlexureCheck.run(input, params) ─► FlexureResult (con traza)
EurocodeParams ────────────────────────────────┘

RunCheck.execute(model, NormId.CE, CheckKind.FLEXURE_ULS)
  └─ CheckCatalog.resolve(CE, FLEXURE_ULS) ─► descriptor
       ├─ descriptor.applicability(model)      → issues? → CheckNotApplicable
       └─ descriptor.prepare_and_run(model)    → preparador + run → FlexureResult
```

## Archivos a crear

```
src/placas_alveolares/
  domain/
    units.py                              # docstring de la convención + constantes (N_PER_KN, MM_PER_M)
    model/
      geometry.py                         # Point, Contour, SectionGeometry(outer, holes), rectangle()
      materials.py                        # Concrete(fck, fcm, ecm), ReinforcingSteel(fyk, es)
      section.py                          # ReinforcementLayer(area, depth), Section(geometry, concrete, layers)
      actions.py                          # InternalForces(n, m_y)
      model.py                            # StructuralModel(section, actions)
    mechanics/
      laws.py                             # Protocol StressStrainLaw
      generic_laws.py                     # ElasticLaw (lineal) — usado por pruebas de mecánica
      section_properties.py               # area(), centroid_y(), second_moment_area()
    checking/
      kinds.py                            # CheckKind, NormId
      results.py                          # CalcStep, CheckResult
      check.py                            # Protocol Check[I,P,R], ApplicabilityIssue
      trace.py                            # DetailLevel, TraceBuilder
  norms/
    eurocode/
      params.py                           # EurocodeParams, ClauseRefs
      inputs.py                           # FlexureInput
      flexure.py                          # FlexureResult, run_flexure(), prepare_flexure(), applicability_flexure()
      module.py                           # register(catalog)
  norms/ce/
    module.py                             # register(): registra eurocode/flexure bajo NormId.CE con ClauseRefs CE
  application/
    catalog.py                            # CheckDescriptor, CheckCatalog, make_descriptor()
    use_cases/
      run_check.py                        # RunCheck + excepciones
      compare_norms.py                    # CompareNorms
tests/
  unit/domain/test_section_properties.py
  unit/norms/test_eurocode_flexure.py
  unit/application/test_catalog.py
  integration/test_run_check_ce_flexure.py
```

## Contratos (firma prevista)

### Traza y resultado

```python
class DetailLevel(StrEnum):
    SUMMARY = "summary"; STANDARD = "standard"; FULL = "full"

@dataclass(frozen=True, slots=True)
class CalcStep:
    label: str; symbol: str; value: float; unit: str
    clause: str | None = None
    children: tuple[CalcStep, ...] = ()

@dataclass(frozen=True, slots=True)
class CheckResult:
    ratio: float; passed: bool; clause: str
    steps: tuple[CalcStep, ...]
```

`TraceBuilder` acumula pasos y expone `.build() -> tuple[CalcStep, ...]`; respeta `DetailLevel`.

### Comprobación

```python
class Check(Protocol[I, P, R]):
    def run(self, data: I, params: P) -> R: ...

@dataclass(frozen=True, slots=True)
class ApplicabilityIssue:
    code: str; message: str
```

### Norma eurocódigo

```python
@dataclass(frozen=True, slots=True)
class EurocodeParams:
    gamma_c: float = 1.5
    gamma_s: float = 1.15
    lambda_: float = 0.8     # fck <= 50 MPa
    eta: float = 1.0

@dataclass(frozen=True, slots=True)
class ClauseRefs:
    flexure: str = "CE / EC2, flexión simple ELU (confirmar)"   # provisional

@dataclass(frozen=True, slots=True)
class FlexureInput:
    b: float; d: float; a_s: float; fck: float; fyk: float; m_ed: float

@dataclass(frozen=True, slots=True)
class FlexureResult(CheckResult):
    m_rd: float; x: float; z: float

def run_flexure(data: FlexureInput, params: EurocodeParams) -> FlexureResult: ...
def prepare_flexure(model: StructuralModel, params: EurocodeParams) -> FlexureInput: ...
def applicability_flexure(model: StructuralModel) -> tuple[ApplicabilityIssue, ...]: ...
```

Fórmulas a implementar (unidades N/mm/MPa; justificación teórica en
[`bases_calculo.md` §3](bases_calculo.md#3-leyes-constitutivas-y-bloque-rectangular)):

```
fcd = fck / gamma_c
fyd = fyk / gamma_s
x   = a_s * fyd / (lambda_ * b * fcd)      # lambda_ se usa como 0.8 en prof. de bloque
z   = d - lambda_/2 * x                     # lambda_/2 = 0.4
m_rd = a_s * fyd * z
ratio = m_ed / m_rd
```

La traza emite pasos para `fcd`, `fyd`, `x`, `z`, `m_rd` con su cláusula.

### Catálogo

```python
@dataclass(frozen=True)
class CheckDescriptor:
    kind: CheckKind; norm: NormId; name: str
    applicability: Callable[[StructuralModel], tuple[ApplicabilityIssue, ...]]
    default_params: Callable[[], object]
    prepare_and_run: Callable[[StructuralModel, object], CheckResult]
    run_direct: Callable[[object, object], CheckResult]

def make_descriptor(
    *, kind: CheckKind, norm: NormId, name: str,
    check: Check[I, P, R],
    prepare: Callable[[StructuralModel, P], I],
    applicability: Callable[[StructuralModel], tuple[ApplicabilityIssue, ...]],
    default_params: Callable[[], P],
) -> CheckDescriptor: ...   # cierra el tipado; 'object' queda confinado aquí
```

### Casos de uso

```python
class CheckNotAvailable(Exception): ...
class CheckNotApplicable(Exception):
    def __init__(self, issues: tuple[ApplicabilityIssue, ...]) -> None: ...

class RunCheck:
    def __init__(self, repo: ModelRepository, catalog: CheckCatalog) -> None: ...
    def execute(self, model_id: ModelId, norm: NormId, kind: CheckKind) -> CheckResult: ...

class CompareNorms:
    def __init__(self, repo: ModelRepository, catalog: CheckCatalog) -> None: ...
    def execute(self, model_id: ModelId, kind: CheckKind) -> list[tuple[NormId, CheckResult]]: ...
```

`ModelRepository` es un puerto mínimo (`get(model_id) -> StructuralModel`); para este milestone se usa un repositorio en memoria en los tests.

## Registro en el composition root

```python
# main.py (fragmento)
from placas_alveolares.norms import ce as ce_norm
from placas_alveolares.application.catalog import CheckCatalog

def build_catalog() -> CheckCatalog:
    catalog = CheckCatalog()
    ce_norm.register(catalog)
    return catalog
```

Añadir otra norma = una línea aquí. Ningún caso de uso cambia.

## Estrategia de pruebas

- `test_section_properties.py`: rectángulo 300×500 → `A = 150000 mm²`, centro y `I` frente a fórmulas analíticas.
- `test_eurocode_flexure.py`: ejemplo de referencia de `spec.md` llamando a `run_flexure` con escalares; se asertan `m_rd`, `x`, `z`, `ratio`, `passed` y la **presencia de los pasos** `fcd`, `fyd`, `x`, `z`, `m_rd`.
- `test_catalog.py`: registro y resolución `(CE, FLEXURE_ULS)`; resolución inexistente → `None`.
- `test_run_check_ce_flexure.py`: modelo → `RunCheck.execute` → resultado; modelo no soportado → `CheckNotApplicable` con motivo.
- `test_compare_norms.py`: con una sola norma devuelve una fila.

## Orden de implementación

1. `domain/model` + `domain/units` + `domain/mechanics` (leyes, propiedades).
2. `domain/checking` (kinds, results, check, trace).
3. `norms/eurocode` (params, inputs, flexure, módulo).
4. `application/catalog` + `make_descriptor`.
5. `application/use_cases` (puerto `ModelRepository`, `RunCheck`, `CompareNorms`).
6. `norms/ce/module.py` + registro en `main.py`.
7. Tests y ajuste; `pyright` y `pytest` en verde.
