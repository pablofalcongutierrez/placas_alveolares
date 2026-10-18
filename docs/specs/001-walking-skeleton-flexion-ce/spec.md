# Milestone 001 — Walking skeleton: flexión ELU bajo Código Estructural

## Objetivo

Recorrer **una vez y de punta a punta** el flujo completo de la arquitectura (modelo → motores → catálogo → comprobación → resultado con traza), con la comprobación más sencilla posible: **flexión simple ELU de una sección rectangular armada, según la familia eurocódigo (Código Estructural)**.

El propósito no es cubrir un caso realista completo, sino **fijar y validar los contratos** (check puro, catálogo, preparador, traza, caso de uso) con un ejemplo cuya respuesta se conoce por cálculo manual. Todo lo que se añada después reutilizará estos contratos.

> **Bases de cálculo:** los fundamentos teóricos (sección plana de Bernoulli–Navier, sistema de ejes y convención de signos, leyes constitutivas y bloque rectangular) están en [`bases_calculo.md`](bases_calculo.md). El diseño técnico, en [`plan.md`](plan.md); el checklist, en [`tasks.md`](tasks.md).

## Alcance

### Incluye
- Modelo estructural mínimo: geometría rectangular (tipo con soporte de huecos, sin usarlos aún), hormigón (`fck`), acero (`fyk`), armadura (una capa a tracción) y acciones (`N`, `M`).
- Propiedades seccionales básicas (área, centro de gravedad, inercia).
- Contratos de comprobación: `Check`, `CheckResult`, `CalcStep`, `TraceBuilder`, `DetailLevel`, `CheckKind`, `NormId`.
- Catálogo de comprobaciones con descriptores y registro.
- Comprobación de flexión ELU eurocódigo (`FlexureCheck`) con bloque rectangular.
- Preparador modelo → entrada y función de aplicabilidad.
- Casos de uso `run_check` y `compare_norms`.
- Registro de la norma en el composition root.
- Informe de traza en texto (mínimo) para verificación manual.

### No incluye (se abordará en milestones posteriores)
- Split formal CE/EC2 con parámetros nacionales diferenciados (milestone 002).
- Cortante, fisuración, ELS, pretensado, evolución temporal.
- Solver de deformaciones general por fibras (aquí la comprobación usa el equilibrio del bloque rectangular).
- Persistencia del modelo (se construye el modelo en memoria/tests).
- UI completa (se valida vía casos de uso y tests).

## Requisitos funcionales

- **RF-1** — Existe un modelo estructural mínimo construible en código y validable por tipos.
- **RF-2** — La comprobación de flexión recibe solo su dataclass de entrada y su dataclass de parámetros (nunca el modelo).
- **RF-3** — El resultado expone `ratio`, `passed`, `clause` y una traza de `CalcStep` con símbolo, valor, unidad y cláusula.
- **RF-4** — El catálogo resuelve `(NormId.CE, CheckKind.FLEXURE_ULS)` sin ningún condicional por norma en el caso de uso.
- **RF-5** — Un preparador traduce modelo → entrada y una función de aplicabilidad detecta modelos no soportados, devolviendo motivos legibles.
- **RF-6** — `compare_norms` devuelve una fila por norma disponible para una comprobación (con una sola norma, una fila).
- **RF-7** — La norma se registra **únicamente** en el composition root; `domain` y `application` no la importan.

## Ejemplo de referencia de validación

Sección rectangular armada a flexión simple:

| Parámetro | Valor |
|---|---|
| Ancho `b` | 300 mm |
| Canto útil `d` | 450 mm |
| Armadura a tracción `As` | 1500 mm² |
| Hormigón `fck` | 30 MPa |
| Acero `fyk` | 500 MPa |
| Momento de cálculo `MEd` | 200 kN·m = 2,0·10⁸ N·mm |

Parámetros eurocódigo (valores recomendados): `γc = 1,5`, `γs = 1,15` → `fcd = 20 MPa`, `fyd = 434,78 MPa`. Bloque rectangular `λ = 0,8`, `η = 1,0`.

Resultados esperados (tolerancia ±0,5 %):

| Magnitud | Expresión | Valor |
|---|---|---|
| Profundidad del bloque `x` | `As·fyd / (0,8·b·fcd)` | 135,87 mm |
| Brazo `z` | `d − 0,4·x` | 395,65 mm |
| Momento resistido `MRd` | `As·fyd·z` | 2,5803·10⁸ N·mm ≈ 258,0 kN·m |
| `x/d` | — | 0,302 (dúctil) |
| Ratio | `MEd / MRd` | 0,775 |
| Veredicto | — | **cumple** |

> Nota: la comprobación debe reproducir además el valor de `fcd`, `fyd` y `x` como pasos de traza.

## Criterios de aceptación

- **CA-1** — `pytest` verde, incluida la prueba del ejemplo de referencia anterior.
- **CA-2** — `pyright` (modo `strict`) limpio en `src`.
- **CA-3** — El test de la comprobación llama a `run(input, params)` con escalares, **sin construir el modelo**.
- **CA-4** — El caso de uso resuelve la comprobación a través del catálogo y **no contiene** ninguna referencia a `norms`.
- **CA-5** — `grep` no encuentra en `domain/` ni en `application/` ningún `import` de `norms`.
- **CA-6** — La traza del ejemplo incluye `fcd`, `fyd`, `x`, `z` y `MRd`, cada uno con unidad y cláusula.
- **CA-7** — Un modelo no soportado (p. ej. sección no rectangular) produce un `ApplicabilityIssue` legible, no una excepción de tipado.
- **CA-8** — `rg "if norma|NormId\." src/placas_alveolares/application` no muestra condicionales por norma (solo uso del identificador como clave).

## Riesgos y decisiones abiertas

- **Número de cláusula del CE**: las etiquetas `clause` se rellenan provisionalmente y deben confirmarse contra el articulado vigente del Código Estructural antes de cerrar el milestone.
- **Alcance del solver mecánico**: en este milestone la comprobación usa el equilibrio del bloque rectangular; el solver general de deformaciones queda para más adelante sin alterar los contratos.
