# ADR 0005 — Traza de cálculos auxiliares

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0002](0002-checks-funciones-puras-tipadas.md)

## Contexto

Se quiere que de cada comprobación puedan extraerse cuantos cálculos auxiliares se desee: valores intermedios, fórmulas aplicadas, cláusulas normativas. Estos auxiliares sirven para tres consumidores distintos: el informe/memoria de cálculo (justificación), la reutilización programática (otro cálculo necesita un valor intermedio) y la depuración/verificación. Hay que hacerlo sin acoplar el dominio a un formato de presentación.

## Decisión

El resultado base incluye una **traza** de pasos como datos inmutables:

```python
@dataclass(frozen=True, slots=True)
class CalcStep:
    label: str; symbol: str; value: float; unit: str
    clause: str | None = None
    children: tuple[CalcStep, ...] = ()     # sub-cálculos anidados

@dataclass(frozen=True, slots=True)
class CheckResult:
    ratio: float
    passed: bool
    clause: str
    steps: tuple[CalcStep, ...]
```

Reglas:

- **Auxiliar para leer** → `CalcStep`. **Auxiliar para calcular con él** → campo tipado del resultado específico.
- `DetailLevel` (`SUMMARY` / `STANDARD` / `FULL`) permite controlar la granularidad emitida; por defecto `STANDARD`.
- La **presentación** (LaTeX, HTML, expresión con números sustituidos) la produce la capa de informe a partir de los datos del paso; el dominio no genera cadenas de formato.
- Los motores iterativos (solver de fibras, integración temporal) emiten solo el resumen convergido, nunca un paso por iteración.

Se ofrece un `TraceBuilder` (`domain/checking/trace.py`) con helpers para reducir el coste de autoría y unificar el estilo entre normas.

## Alternativas consideradas

- **Sin traza; solo el resultado final.** Rechazada: imposibilita la justificación de comprobaciones y la verificación paso a paso.
- **Registrar auxiliares en un diccionario genérico.** Rechazada: pierde tipado y significado.
- **DSL/pipeline de pasos compuestos reutilizables.** Rechazada por complejidad prematura: la traza declarativa aporta la mayor parte del beneficio (justificación y depuración) con muy poco coste.
- **Traza anidada como datos (elegida)**, con renderizado delegado a la capa de informe.

## Consecuencias

- Cada comprobación construye su propia traza: es trabajo mecánico de autoría, no complejidad arquitectónica, y el `TraceBuilder` lo simplifica.
- Los tests pueden asertar pasos intermedios, no solo el resultado final.
- La serialización es directa (dataclasses `frozen`), útil para persistencia y para el informe del TFM.
- Añadir auxiliares a una comprobación no afecta a ninguna otra ni a los contratos.

## Notas de implementación

Decisión esencial (la traza forma parte del contrato de resultado). La forma exacta de la expresión sustituida y el formato del informe son detalles de la capa de presentación.
