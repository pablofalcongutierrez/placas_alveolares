# ADR 0002 — Comprobaciones como funciones puras con entradas y parámetros tipados

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0001](0001-frontera-mecanica-fisica-vs-normativa.md), [0003](0003-catalogo-plugins-sin-switch-central.md)

## Contexto

Cada comprobación y cada norma difieren en los datos que necesitan: unas requieren la sección y un estado de esfuerzos; otras, una historia de cargas. No se quiere imponer un conjunto universal de parámetros, ni que los algoritmos "rebusquen" en todo el modelo del proyecto. Al mismo tiempo se exige tipado estricto (Pyright `strict`), autocompletado y detección temprana de errores, evitando `**kwargs` y diccionarios genéricos.

## Decisión

Cada comprobación es una **función pura de números**:

```python
class Check(Protocol[I, P, R]):
    def run(self, data: I, params: P) -> R: ...
```

- `data: I` es un dataclass `frozen` **específico** de la comprobación, con los datos físicos mínimos que necesita.
- `params: P` es un dataclass `frozen` **específico** de la norma, con sus coeficientes.
- `R` es un resultado específico que hereda de la base mínima `CheckResult`.

La traducción modelo → entrada la realiza un **preparador** separado. La comprobación nunca recibe la entidad `Section` ni accede al proyecto.

## Alternativas consideradas

- **Jerarquía de clases por norma** (`ShearCheck` abstracto → `EC2ShearCheck`, `ACIShearCheck`). Rechazada como mecanismo principal: fuerza una abstracción común que no existe (las normas no ofrecen el mismo conjunto de comprobaciones ni las mismas entradas) y genera explosión combinatoria tipo×norma.
- **Diccionarios de parámetros / `**kwargs`.** Rechazada: destruye el tipado, el autocompletado y la detección temprana.
- **Pasar el modelo estructural completo a cada `run`.** Rechazada: acopla cada algoritmo a la evolución del modelo y dificulta las pruebas.
- **Funciones puras con dataclasses específicos (elegida).**

## Consecuencias

- Las comprobaciones se prueban contra ejemplos de bibliografía **sin construir un modelo completo**, lo que da tests rápidos y precisos.
- Añadir un parámetro a una norma es un cambio aditivo en su dataclass de parámetros, sin efecto en las demás normas.
- Aparece código de "preparación" (preparadores). Se asume como responsabilidad separada y explícita.
- La herencia se reserva a los **resultados** (`ShearResult(CheckResult)`), nunca a los algoritmos.

## Notas de implementación

Decisión esencial. El número de dataclasses (input, params, result por comprobación) es coste aceptado a cambio de tipado y aislamiento. Compartir VOs de `domain` entre inputs evita duplicación sin volver a un "input universal".
