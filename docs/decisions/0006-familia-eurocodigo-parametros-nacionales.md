# ADR 0006 — Familia eurocódigo con parámetros nacionales (CE / EC2)

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0001](0001-frontera-mecanica-fisica-vs-normativa.md), [0003](0003-catalogo-plugins-sin-switch-central.md)

## Contexto

Las primeras normativas objetivo son el **Código Estructural** (CE) y, específicamente para placas alveolares, el cortante de la norma de producto **EN 1168**. El CE no es independiente del Eurocódigo 2: es la familia eurocódigo aplicada con los parámetros nacionales españoles (Anexo Nacional), con la misma estructura algorítmica y, en su mayoría, las mismas fórmulas. Implementar CE y EC2 como dos conjuntos de código independientes duplicaría la mecánica de comprobación; forzar una única norma, en cambio, perdería las diferencias nacionales.

## Decisión

La familia eurocódigo se implementa **una sola vez** en `norms/eurocode/`, y la diferencia entre normas es **dato**:

- Los **coeficientes** (γc, γs, αcc…) residen en un dataclass de parámetros (`EurocodeParams`).
- Las **referencias de cláusula** (`ClauseRefs`) que alimentan `CalcStep.clause` también son datos.
- `norms/ce/module.py` registra las implementaciones bajo `NormId.CE` con los valores del Anexo Nacional español y las etiquetas del CE.
- `norms/ec2/module.py` registra las mismas implementaciones bajo `NormId.EC2` con los valores recomendados del eurocódigo.
- Solo donde el CE diverge **sustancialmente** (método distinto, no solo coeficientes) se crea un check específico en `norms/ce/`.

Este es un caso **legítimo** del patrón "comprobación paramétrica compartida": idéntica estructura algorítmica, distintos coeficientes y referencias. No se debe confundir con forzar una abstracción común entre normas de estructura diferente (p. ej. EC2 y ACI 318), que se mantienen separadas.

## Alternativas consideradas

- **CE y EC2 como implementaciones independientes.** Rechazada: duplicación innecesaria y divergencia de mantenimiento.
- **Una sola norma "eurocódigo" sin distinguir CE/EC2.** Rechazada: se pierde la capacidad de comparar el efecto de los parámetros nacionales y de citar correctamente cada cláusula.
- **Familia eurocódigo parametrizada (elegida).**

## Consecuencias

- La comparación **CE vs EC2** (misma sección, mismos coeficientes salvo los nacionales) es directa y produce material analítico para la memoria del TFM.
- Añadir otra norma basada en el eurocódigo (p. ej. un país distinto) es añadir un módulo de parámetros y un registro.
- Exige disciplina: la reutilización solo es válida cuando la estructura del algoritmo es **idéntica**, no meramente parecida.

## Normas de producto

`norms/en1168/` sigue el mismo patrón de plugin, pero ofrece un **subconjunto** de comprobaciones (cortante específico de placa alveolar) con `applicability` restringida a secciones alveolares pretensadas. Demuestra que una norma no necesita cubrir el mismo conjunto de verificaciones que las demás.

## Notas de implementación

Decisión esencial para la estructura de `norms/`. La frontera exacta entre "mismo algoritmo con otros coeficientes" y "algoritmo distinto" se decide caso por caso; ante la duda, implementaciones separadas.
