# ADR 0001 — Frontera entre mecánica física y reglas normativas

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0006](0006-familia-eurocodigo-parametros-nacionales.md)

## Contexto

La herramienta debe incorporar progresivamente normas (CE, EC2, EN 1168, EHE-08, ACI 318) y tipos de cálculo (propiedades seccionales, respuesta mecánica, flexión, cortante, fisuración, pretensado evolutivo). Las normas no solo cambian fórmulas: cambian hipótesis, leyes constitutivas, coeficientes y criterios de verificación. Se necesita decidir qué parte es común y qué parte es específica de cada norma sin duplicar la mecánica ni forzar abstracciones falsas.

## Decisión

Se establece una frontera explícita:

> La mecánica es común; las **leyes constitutivas**, los **coeficientes** y los **criterios de verificación** son normativos.

- Los **motores mecánicos** (equilibrio de secciones, compatibilidad deformacional, integración de tensiones sobre fibras, propiedades geométricas, momento-curvatura, evolución temporal) viven en `domain/mechanics` y reciben las leyes por **inyección** mediante protocolos (`StressStrainLaw`, `CreepShrinkageModel`).
- Las **leyes normativas** (parábola-rectángulo, bloque de Whitney, fluencia del Anexo B, ACI 209) viven en `norms/*/laws.py`.
- Las **leyes físicas genéricas** (elástica, elastoplástica) viven en `domain/mechanics/generic_laws.py`, permitiendo analizar secciones sin ninguna norma.

## Alternativas consideradas

- **Motores específicos por norma (un solver de EC2, otro del ACI).** Rechazada: duplica la mecánica y hace que un error de equilibrio haya que corregirlo en N sitios.
- **Un único solver con condicionales internos según la norma.** Rechazada: acopla el núcleo a las normas concretas y contradice la regla de dependencias.
- **Protocolo de leyes inyectadas (elegida).** Coste: hay que definir bien la interfaz de las leyes y preparar las implementaciones por norma. Beneficio: mecánica única, testeable de forma independiente y reutilizable por todas las normas.

## Consecuencias

- Los motores se pueden probar contra soluciones analíticas sin depender de ninguna norma.
- Añadir una norma no toca la mecánica; solo aporta leyes y parámetros.
- Aparecen "costuras" donde el modelo físico puede depender de la norma (p. ej. leyes cuyo parámetro de entrada es un valor característico): se resuelven inyectando el valor ya resuelto en la ley, no consultando la norma desde el motor.

## Notas de implementación

Este ADR fija una decisión **esencial** y difícil de revertir: determina los contratos de `domain/mechanics`. No fija detalles como el número exacto de protocolos ni su firma, que pueden refinarse.
