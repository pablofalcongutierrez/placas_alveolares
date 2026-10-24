# Tareas — Milestone 001

Marca cada tarea al completarla. Antes de cerrar: `pyright` limpio y `pytest` verde.

> Contexto: [`spec.md`](spec.md) · [`plan.md`](plan.md) · [`bases_calculo.md`](bases_calculo.md)

## Bases de cálculo (documentación)

- [ ] Colocar `ejes_seccion_2d.png` y `ejes_seccion_3d.png` en `resources/images/specs/001/`.
- [ ] Revisar que [`bases_calculo.md`](bases_calculo.md) es coherente con la convención de ejes y signos implementada.

## Modelo y mecánica (domain)

### Modelo geométrico por componentes, fases y adherencia (ADR 0007)

- [x] `domain/unidades.py` — documentar la convención mm/N/MPa/N·mm y constantes de conversión.
- [x] `domain/model/geometria.py` — `Punto`, `Contorno`, `GeometriaContorno`, helpers `rectangulo()` y `circulo()` (cordones poligonizados).
- [x] `domain/model/materiales.py` — `Hormigon`, `AceroArmadura`, `AceroPretensado`, `modulo_elastico()` (propiedades físicas, sin ley constitutiva).
- [x] `domain/model/seccion.py` — `CondicionAdherencia`, `ComponenteSeccion`, `Seccion`.
- [x] `domain/model/fases.py` — `Fase`, `componentes_activos()`, `componentes_adheridos()`.
- [x] `domain/model/acciones.py` — `EsfuerzosInternos(n, m_y, m_z)`. 
- [x] `domain/model/modelo.py` — `ModeloEstructural(seccion, acciones, fases, fase_activa)`.

### Mallado y cuadratura (ADR 0008)

- [x] `domain/mechanics/mallado.py` — `Triangulo`, `mallar()` (mapbox-earcut aislado, validación de huecos).
- [x] `domain/mechanics/integracion.py` — `EvaluacionGauss`, `ReglaCuadratura`, `Regla1Punto`, `Regla3Puntos`, `integrar()`.
- [x] `domain/mechanics/propiedades_seccion.py` — `PropiedadesSeccion(area, y_cdg, z_cdg, i_y, i_z, i_yz)`, `propiedades_geometricas()` (malla + Gauss).

### Leyes constitutivas (ADR 0001)

- [x] `domain/mechanics/laws.py` — `Protocol LeyTensionDeformacion`.
- [x] `domain/mechanics/generic_laws.py` — `LeyElastica` y `LeyElastoplastica`.

## Contratos de comprobación (domain)

- [ ] `domain/checking/kinds.py` — `CheckKind` (`FLEXURE_ULS`, …), `NormId` (`CE`, `EC2`, …).
- [ ] `domain/checking/results.py` — `CalcStep`, `CheckResult`.
- [ ] `domain/checking/check.py` — `Protocol Check[I,P,R]`, `ApplicabilityIssue`.
- [ ] `domain/checking/trace.py` — `DetailLevel`, `TraceBuilder`.

## Norma eurocódigo (norms)

- [x] `norms/eurocode/laws.py` — leyes σ–ε del hormigón (lineal, parábola-rectángulo, bilineal y general no lineal) y Tabla 3.1.
- [ ] `norms/eurocode/params.py` — `EurocodeParams`, `ClauseRefs`.
- [ ] `norms/eurocode/inputs.py` — `FlexureInput`.
- [ ] `norms/eurocode/flexure.py` — `FlexureResult`, `run_flexure`, `prepare_flexure`, `applicability_flexure`.
- [ ] `norms/eurocode/module.py` — factoría/registro reutilizable.

## Aplicación

- [ ] `application/catalog.py` — `CheckDescriptor`, `CheckCatalog`, `make_descriptor`.
- [ ] `application/ports` — `ModelRepository`.
- [ ] `application/use_cases/run_check.py` — `RunCheck`, `CheckNotAvailable`, `CheckNotApplicable`.
- [ ] `application/use_cases/compare_norms.py` — `CompareNorms`.

## Composición

- [ ] `norms/ce/module.py` — `register(catalog)` bajo `NormId.CE`.
- [ ] `main.py` — `build_catalog()` + registro de `ce`.

## Pruebas

- [x] `tests/unit/domain/test_geometria.py` — validación de `Contorno`, `rectangulo()` y `circulo()`.
- [x] `tests/unit/domain/test_seccion.py` — invariantes de `Seccion` y `ModeloEstructural`.
- [x] `tests/unit/domain/test_fases.py` — activación por fase y por adherencia.
- [x] `tests/unit/domain/test_mallado.py` — triangulación con/sin huecos y círculo.
- [x] `tests/unit/domain/test_integracion.py` — reglas de cuadratura e integrales exactas.
- [x] `tests/unit/domain/test_propiedades_seccion.py` — área, cdg e inercia (300×500, hueco y círculo).
- [x] `tests/unit/domain/test_generic_laws.py` — leyes elástica y elastoplástica.
- [x] `tests/unit/norms/eurocode/test_laws.py` — Tabla 3.1, las cuatro leyes y equivalencia con el bloque rectangular.
- [ ] `tests/unit/norms/eurocode/test_flexure.py` — ejemplo de referencia (MRd ≈ 258,0 kN·m, ratio ≈ 0,775) y pasos de traza.
- [ ] `tests/unit/application/test_catalog.py` — resolución existente e inexistente.
- [ ] `tests/integration/test_run_check_ce_flexure.py` — flujo completo y `CheckNotApplicable`.
- [ ] `tests/integration/test_compare_norms.py` — una fila con una norma.

## Cierre

- [ ] `pyright` limpio (modo strict).
- [ ] `pytest` verde.
- [ ] Verificar CA-5: sin imports de `norms` en `domain/` ni `application/`.
- [ ] Confirmar las etiquetas de cláusula del CE contra el articulado vigente.
