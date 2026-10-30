# Arquitectura

## Capas y regla de dependencias

```
presentation ─────────────┐
infrastructure ──► application ──► domain ◄── norms ◄── composition root (main/container)
```

- `domain`: modelo estructural, mecánica, estados y **contratos de comprobación**. **No depende de nada.**
- `norms`: **plugins normativos** (EC2, Código Estructural, EN 1168…). Dependen solo de `domain`. Cada norma es un paquete autocontenido.
- `application`: catálogo de comprobaciones, casos de uso, DTOs y **puertos** (interfaces). Depende solo de `domain`. **No importa `norms`.**
- `infrastructure`: adaptadores que implementan los puertos (SQLAlchemy, export, servicios externos), configuración y arranque. Depende de `application`/`domain`.
- `presentation`: UI PySide y controladores (MVP). Depende de `application`.
- `main.py` (composition root): **único** punto que importa los paquetes de normas y los registra en el catálogo.

Regla: **las dependencias apuntan siempre hacia dentro**. `norms` se sitúa junto a `infrastructure` como capa de implementación (ambas realizan contratos internos); ninguna es conocida por el núcleo.

## Estructura

```
src/placas_alveolares/
  main.py                  # entrypoint: composición + registro de normas + QApplication
  __main__.py              # `python -m placas_alveolares`
  domain/
    errores.py             # jerarquía de errores: ErrorDominio, ErrorValidacion, ErrorCalculo
    model/                 # modelo estructural (agnóstico de norma)
      geometria.py         #   Punto, Contorno, GeometriaContorno; helpers rectangulo(), circulo()
      materiales.py        #   Hormigon, AceroArmadura, AceroPretensado (propiedades físicas)
      seccion.py           #   Seccion, ComponenteSeccion, CondicionAdherencia
      acciones.py          #   EsfuerzosInternos
      fases.py             #   Fase, activación por fase y por adherencia
      modelo.py            #   ModeloEstructural
    mechanics/             # motores físicos (funciones puras)
      mallado.py           #   Triangulo, mallar() (mapbox-earcut, aislado)
      integracion.py       #   ReglaCuadratura, Regla1Punto/Regla3Puntos, integrar()
      propiedades_seccion.py   # PropiedadesSeccion, propiedades_geometricas()
      laws.py              #   Protocolos: LeyTensionDeformacion, ModeloFluenciaRetraccion
      generic_laws.py      #   leyes físicas: elástica, elastoplástica
      strain_solver.py     #   (N, M) → plano de deformaciones en equilibrio
      moment_curvature.py
      time_evolution.py    #   integración temporal con modelo inyectado
    numerics/              # solvers genéricos, independientes de la física
      problema.py          #   ProblemaNoLineal y ProblemaParametrizado
      newton.py            #   Newton (F(x) = 0)
      diferencias_finitas.py
      continuacion/        #   contratos de continuación (λ, restricción de arco)
    value_objects/         # objetos de valor sin identidad
      coeficientes_parciales.py   # CoeficientesParciales (forma; valores en norms)
    state/                 # StrainProfile, StressResultants, SectionState, History
    checking/              # contratos de comprobación
      kinds.py             #   CheckKind (vocabulario), NormId
      results.py           #   CheckResult (base), CalcStep
      check.py             #   Protocol Check[I, P, R], ApplicabilityIssue
      trace.py             #   TraceBuilder, DetailLevel
    unidades.py            # convención de unidades del núcleo
  norms/
    eurocode/              # implementaciones de la familia eurocódigo
    ce/                    # Código Estructural (parámetros nacionales + registro)
      materiales/          #   tablas abiertas: aceros pasivos, hormigones, pretensados
      coeficientes.py      #   juegos de γc y γs
    ec2/                   # Eurocódigo 2 (valores recomendados)
    en1168/                # placa alveolar: cortante específico
    _shared/               # fórmulas normativas realmente repetidas (regla de tres)
  application/
    errores.py             # ErrorAplicacion, EntradaProtegida, EntradaDuplicada
    catalog.py             # CheckCatalog + descriptores
    almacen_catalogo.py    # AlmacenCatalogo[T]: implementación genérica en memoria
    use_cases/             # run_check, compare_norms, analyze_section
    dtos/
    ports/
      catalogo.py          # Catalogo[T]: contrato genérico de biblioteca
      entradas_catalogo.py # EntradaCatalogo[T], OrigenEntrada
  infrastructure/{config,persistence,export,external_services}
  presentation/{views,controllers,widgets}
migrations/                # Alembic
resources/                 # datos estáticos
tests/{unit,integration,acceptance}
```

## Núcleo de cálculo seccional

### Principio rector: mecánica física vs. reglas normativas

> La mecánica no es normativa; las **leyes constitutivas**, los **coeficientes** y los **criterios de verificación** sí lo son.

El equilibrio, la compatibilidad deformacional, la integración de tensiones sobre fibras y la evolución temporal bajo un modelo de fluencia son física común. La parábola-rectángulo, el bloque de Whitney, los coeficientes γ/φ, las fórmulas de `V_Rd,c` y los límites de fisuración son normativos. Por tanto:

- Los **motores mecánicos** viven en `domain/mechanics` y reciben las leyes constitutivas **por inyección** (`LeyTensionDeformacion`, `ModeloFluenciaRetraccion`).
- Las **leyes normativas** viven en `norms/*/laws.py`. Las leyes físicas genéricas (elástica, elastoplástica) viven en `domain/mechanics/generic_laws.py` y permiten analizar sin ninguna norma.

Detalle y alternativas en [`decisions/0001-frontera-mecanica-fisica-vs-normativa.md`](decisions/0001-frontera-mecanica-fisica-vs-normativa.md).

### Conceptos y responsabilidades

| Concepto | Responsabilidad | NO conoce |
|---|---|---|
| Modelo estructural | Geometría, materiales, armaduras, tendones, acciones, fases | Normas, comprobaciones |
| Leyes constitutivas | σ–ε, fluencia, retracción | Secciones, esfuerzos |
| Motores mecánicos | Propiedades, solver deformacional, M–κ, evolución temporal | De qué norma vienen las leyes |
| Estados físicos | Resultados de análisis; entrada de comprobaciones | Normas |
| Comprobación (Check) | Regla normativa pura: datos tipados + parámetros → resultado trazable | El modelo del proyecto, la UI |
| Parámetros normativos | Coeficientes tipados e inmutables de una norma | Qué check los usa |
| Entrada de check | Dataclass mínimo y específico de cada check | El modelo completo |
| Preparador | Traduce modelo → entrada de check (invocando motores si procede) | Cómo se ejecuta el check |
| Resultado y traza | `ratio`, veredicto, cláusula y pasos de cálculo | Normas concretas |
| Catálogo | Registro y resolución `(norma, tipo) → descriptor` | Fórmulas |
| Casos de uso | Orquestan: cargar → aplicabilidad → preparar → ejecutar → informe | Normas concretas |

### Solvers numéricos desacoplados

Los métodos numéricos viven en `domain/numerics` y no conocen la física. Se
distinguen dos familias:

- **Ecuaciones no lineales** (`SolverNoLineal`): resuelven `F(x) = 0`. Newton
  es la primera implementación; ModifiedNewton, DampedNewton y Broyden podrán
  añadirse como clases independientes. La resolución lineal se delega en
  NumPy y el historial de iteraciones queda en el resultado.
- **Continuación** (`SolverContinuacion`): recorren una trayectoria
  `F(u, λ) = 0` con una restricción de arco. El factor de carga `λ` es una
  incógnita, no un parámetro fijo. Los contratos incluyen
  `ProblemaParametrizado` (residuo, `∂F/∂u` y `∂F/∂λ`), `RestriccionArco`,
  `EstadoContinuacion` y `ResultadoContinuacion`. Arc-length se implementará
  como un solver de esta familia y podrá reutilizar cualquier
  `SolverNoLineal` como corrector.

Detalle y alternativas en
[`decisions/0011-solvers-no-lineales-desacoplados.md`](decisions/0011-solvers-no-lineales-desacoplados.md).

### Contratos de comprobación

Una comprobación es una **función pura de números**: no recibe la entidad `Section` ni "busca" en el proyecto. Esto la hace testeable contra ejemplos de bibliografía sin construir un modelo.

```python
# domain/checking/check.py
class Check(Protocol[I, P, R]):
    def run(self, data: I, params: P) -> R: ...

# domain/checking/kinds.py
class CheckKind(StrEnum):
    FLEXURE_ULS = "flexure_uls"
    SHEAR_ULS = "shear_uls"
    CRACK_WIDTH = "crack_width"
    ...

class NormId(StrEnum):
    CE = "ce"; EC2 = "ec2"; EN1168 = "en1168"; ...

# Ejemplo de resultado específico (norms/eurocode/flexure.py)
@dataclass(frozen=True, slots=True)
class FlexureResult(CheckResult):
    m_rd: float
    x: float
    z: float
```

### Catálogo y selección (sin condicional central)

El catálogo almacena descriptores heterogéneos encapsulando el tipado:

```python
# application/catalog.py
@dataclass(frozen=True)
class CheckDescriptor:
    kind: CheckKind
    norm: NormId
    name: str
    applicability: Callable[[StructuralModel], tuple[ApplicabilityIssue, ...]]
    default_params: Callable[[], object]
    prepare_and_run: Callable[[StructuralModel, object], CheckResult]
    run_direct: Callable[[object, object], CheckResult]   # tests/comparaciones

class CheckCatalog:
    def register(self, d: CheckDescriptor) -> None: ...
    def resolve(self, norm: NormId, kind: CheckKind) -> CheckDescriptor | None: ...
    def available(self, norm: NormId | None = None) -> list[CheckDescriptor]: ...
```

Cada norma se declara a sí misma con `register(catalog)`. El caso de uso nunca importa una norma:

```python
def execute(self, model_id, norm: NormId, kind: CheckKind) -> CheckResult:
    model = self._repo.get(model_id)
    d = self._catalog.resolve(norm, kind)
    if d is None: raise CheckNotAvailable(norm, kind)
    issues = d.applicability(model)
    if issues: raise CheckNotApplicable(issues)
    return d.prepare_and_run(model, d.default_params())
```

Detalle y alternativas en [`decisions/0003-catalogo-plugins-sin-switch-central.md`](decisions/0003-catalogo-plugins-sin-switch-central.md).

### Catálogos de datos normativos

Los materiales, los coeficientes y cualquier otra tabla normativa forman **bibliotecas tipadas** con dos fuentes:

- **Presets normativos:** tablas de datos en `norms/<norma>/`. Son dato normativo versionado en código y **de solo lectura**.
- **Entradas de usuario:** datos creados por el usuario, persistentes en la base de datos (milestone de persistencia).

El contrato es un único puerto genérico, `Catalogo[T]`, implementado en memoria por `AlmacenCatalogo[T]`. Cada instancia contiene **un solo tipo de dato** (`Hormigon`, `CoeficientesParciales`, …), de modo que añadir una nueva tabla no exige crear otro puerto ni otro CRUD.

Cada entrada es una `EntradaCatalogo[T]` con:

- `origen`: `NORMATIVO` o `USUARIO`;
- `norma`: `NormId` para presets y `None` para entradas de usuario;
- `edicion` y `referencia`: metadatos opcionales de procedencia;
- `valor`: el dato tipado.

Los presets se identifican por `(NormId, nombre)`, por lo que dos normas pueden compartir designación sin sobrescribirse. Las entradas de usuario son independientes de la norma. `registrar` y `eliminar` solo actúan sobre el espacio de usuario; los intentos de reutilizar un nombre normativo lanzan `EntradaProtegida`, y los presets duplicados lanzan `EntradaDuplicada`.

`application` no importa `norms`: la composición (`main.py`) inyecta los presets ya materializados como tipos del dominio.

Detalle y alternativas en [`decisions/0010-catalogo-generico-datos.md`](decisions/0010-catalogo-generico-datos.md).

### Entradas, preparadores y dependencias entre cálculos

- **Información compartida parcialmente:** los inputs se componen de los mismos VOs/escalares derivados; lo común vive en el modelo y en los motores, no en un "input universal".
- **Datos adicionales:** el input de ese check simplemente tiene más campos; el sistema de tipos impide mezclarlos.
- **Dependencia de resultados previos:** el input incluye el estado que necesita (`SectionState`, `SectionStateHistory`) y el **preparador compone los motores** explícitamente.

Gestión de errores:

| Situación | Mecanismo |
|---|---|
| Campo obligatorio ausente en un input | Error **de tipado** (dataclass sin valor por defecto) — Pyright |
| Invariante de dominio incumplida | `ErrorValidacion` (`GeometriaInvalida`, `MaterialInvalido`, `SeccionInvalida`, `FaseInvalida`, `ModeloInvalido`, `CoeficientesInvalidos`) |
| Intento de modificar un preset normativo | `EntradaProtegida` (`ErrorAplicacion`) |
| El modelo no tiene datos para este check | `ApplicabilityIssue`, evaluado antes de ejecutar |
| Datos inválidos en frontera (importación, formularios) | Validación pydantic en DTOs |
| Fallo numérico (solver no converge) | `ErrorCalculo` (p. ej. `ErrorMallado`) capturado por el caso de uso |

Todas las capas comparten la raíz `ErrorDominio`: cada una define su propia base (`ErrorAplicacion`, `ErrorNorma`, `ErrorInfraestructura`, `ErrorPresentacion`) heredando de ella, de modo que la presentación puede capturar un único tipo raíz. Detalle en [`decisions/0009-errores-tipados-por-capas.md`](decisions/0009-errores-tipados-por-capas.md).

### Resultados y trazabilidad

Base común **mínima**, específica por comprobación, y traza de cálculos auxiliares:

```python
@dataclass(frozen=True, slots=True)
class CalcStep:
    label: str; symbol: str; value: float; unit: str
    clause: str | None = None
    children: tuple[CalcStep, ...] = ()     # sub-cálculos anidados

@dataclass(frozen=True, slots=True)
class CheckResult:
    ratio: float           # demanda/capacidad (Ed/Rd ó Ru/φRn)
    passed: bool
    clause: str
    steps: tuple[CalcStep, ...]
```

- **Común:** `ratio`, `passed`, `clause`, `steps`. Permite informes y comparaciones uniformes entre normas.
- **Específico:** subclases con campos tipados. Nada de diccionarios de "extras".
- **Auxiliar para leer** → `CalcStep`; **auxiliar para calcular con él** → campo tipado del resultado específico.
- **Nivel de detalle:** `DetailLevel` (`SUMMARY` / `STANDARD` / `FULL`) permite controlar cuántos auxiliares se emiten.
- La **presentación** (LaTeX, HTML) es responsabilidad de la capa de informe: el dominio solo produce datos.

Detalle y alternativas en [`decisions/0005-traza-calculos-auxiliares.md`](decisions/0005-traza-calculos-auxiliares.md).

### Unidades

Sistema coherente fijo en todo el núcleo: **mm, N, MPa (N/mm²), N·mm**. Las conversiones se realizan solo en las fronteras (UI, importación, exportación); `CalcStep.unit` etiqueta para presentación. Detalle y alternativas en [`decisions/0004-unidades-convencion-n-mm-mpa.md`](decisions/0004-unidades-convencion-n-mm-mpa.md).

## Normas (plugins)

### Familia eurocódigo

El Código Estructural no es independiente del EC2: es la familia eurocódigo con los parámetros nacionales españoles. Por eso las **implementaciones** residen en `norms/eurocode/` y lo que cambia entre `NormId.CE` y `NormId.EC2` son **datos**: coeficientes y referencias de cláusula (`ClauseRefs`) que alimentan la traza. Solo donde el CE diverge sustancialmente del EC2 se crea un check específico. Detalle en [`decisions/0006-familia-eurocodigo-parametros-nacionales.md`](decisions/0006-familia-eurocodigo-parametros-nacionales.md).

### Normas de producto

Una norma puede ofrecer un subconjunto de comprobaciones. `norms/en1168/` registra solo el cortante específico de placa alveolar, con `applicability` restringida a secciones alveolares pretensadas.

## Configuración

- **Runtime:** `infrastructure/config/settings.py` (pydantic-settings, prefijo `PA_`, lee `.env`).
  - `PA_DATABASE_URL` (por defecto `sqlite:///./placas.db`).
  - Cambiar a PostgreSQL = cambiar solo esa variable.
- **Estático:** carpeta `resources/`, cargada con `importlib.resources`.

## UI (PySide)

- Vistas finas + controladores (presenters) en `presentation/`.
- El catálogo expone qué comprobaciones están disponibles por norma (y su aplicabilidad), de modo que la UI se construye a partir de esa consulta sin conocer las normas.
- Flujo recomendado: Python puro; si se requiere edición visual, `.ui` en `presentation/views/ui/` y generados en `presentation/views/generated/`.

## Tipado

- Pyright en modo `strict` (`[tool.pyright]` en `pyproject.toml`).
- Genéricos + `Protocol` + dataclasses `frozen`/`slots`. Prohibido `**kwargs` y diccionarios genéricos como mecanismo principal.
- Excluye `migrations`, `__pycache__`.

## Pruebas

- `tests/unit/domain`: motores contra soluciones analíticas e **invariantes** (equilibrio de tensiones).
- `tests/unit/norms/<norma>`: ejemplos de referencia llamando a `run` con escalares, sin modelo.
- `tests/unit/application`: preparadores y catálogo.
- `tests/integration`: casos de uso end-to-end y comparación entre normas.
- `tests/acceptance`: flujos completos (UI/controladores).
- `pyright --strict` en CI como puerta estática.

Detalle completo (organización, comandos y convenciones) en [`testing.md`](testing.md).

## Roadmap

1. Walking skeleton: geometría con huecos → propiedades → flexión ELU Código Estructural end-to-end, con traza.
2. Split CE/EC2 (familia eurocódigo) + caso de uso `compare_norms`.
3. Cortante: eurocódigo (CE/EC2) y módulo EN 1168 con aplicabilidad restringida.
4. Pretensado y evolución temporal (pérdidas, transferencia, servicio).
5. ELS: limitación de tensiones y fisuración.
6. Normas adicionales (EHE-08, ACI 318) como validación de extensibilidad.

Las especificaciones de cada milestone viven en [`specs/`](specs/): `spec.md` (qué y por qué), `bases_calculo.md` (fundamentos teóricos, aislados de la implementación y reutilizables en la memoria del TFM), `plan.md` (diseño técnico) y `tasks.md` (checklist).
