# Tareas — Milestone 001

Marca cada tarea al completarla. Antes de cerrar: `pyright` limpio y `pytest` verde.

> Contexto: [`spec.md`](spec.md) · [`plan.md`](plan.md) · [`bases_calculo.md`](bases_calculo.md)

## Bases de cálculo (documentación)

- [ ] Colocar `ejes_seccion_2d.png` y `ejes_seccion_3d.png` en `resources/images/specs/001/`.
- [ ] Revisar que [`bases_calculo.md`](bases_calculo.md) es coherente con la convención de ejes y signos implementada.

## Modelo y mecánica (domain)

- [ ] `domain/units.py` — documentar la convención mm/N/MPa/N·mm y constantes de conversión.
- [ ] `domain/model/geometry.py` — `Point`, `Contour`, `SectionGeometry(outer, holes)` y helper `rectangle(b, h)`.
- [ ] `domain/model/materials.py` — `Concrete`, `ReinforcingSteel` (propiedades físicas).
- [ ] `domain/model/section.py` — `ReinforcementLayer`, `Section`.
- [ ] `domain/model/actions.py` — `InternalForces(n, m_y)`.
- [ ] `domain/model/model.py` — `StructuralModel(section, actions)`.
- [ ] `domain/mechanics/laws.py` — `Protocol StressStrainLaw`.
- [ ] `domain/mechanics/generic_laws.py` — `ElasticLaw`.
- [ ] `domain/mechanics/section_properties.py` — `area`, `centroid_y`, `second_moment_area`.

## Contratos de comprobación (domain)

- [ ] `domain/checking/kinds.py` — `CheckKind` (`FLEXURE_ULS`, …), `NormId` (`CE`, `EC2`, …).
- [ ] `domain/checking/results.py` — `CalcStep`, `CheckResult`.
- [ ] `domain/checking/check.py` — `Protocol Check[I,P,R]`, `ApplicabilityIssue`.
- [ ] `domain/checking/trace.py` — `DetailLevel`, `TraceBuilder`.

## Norma eurocódigo (norms)

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

- [ ] `tests/unit/domain/test_section_properties.py` — área, centro, inercia (300×500).
- [ ] `tests/unit/norms/test_eurocode_flexure.py` — ejemplo de referencia (MRd ≈ 258,0 kN·m, ratio ≈ 0,775) y pasos de traza.
- [ ] `tests/unit/application/test_catalog.py` — resolución existente e inexistente.
- [ ] `tests/integration/test_run_check_ce_flexure.py` — flujo completo y `CheckNotApplicable`.
- [ ] `tests/integration/test_compare_norms.py` — una fila con una norma.

## Cierre

- [ ] `pyright` limpio (modo strict).
- [ ] `pytest` verde.
- [ ] Verificar CA-5: sin imports de `norms` en `domain/` ni `application/`.
- [ ] Confirmar las etiquetas de cláusula del CE contra el articulado vigente.
