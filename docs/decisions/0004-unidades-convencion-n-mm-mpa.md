# ADR 0004 — Convención fija de unidades (mm, N, MPa, N·mm)

- **Estado:** aceptado
- **Fecha:** 2026-10-18

## Contexto

El cálculo estructural maneja magnitudes con unidades físicas (fuerza, longitud, tensión, momento). Mezclar convenciones (kN vs N, m vs mm, MPa vs kN/m²) es una fuente clásica de errores. Se necesita una estrategia de unidades para todo el núcleo de cálculo que sea compatible con el tipado estricto (Pyright `strict`) y eficiente en los bucles de análisis fibra a fibra.

## Decisión

Se adopta una **convención coherente fija** en todo el núcleo:

- Longitud: **mm**
- Fuerza: **N**
- Tensión: **MPa (N/mm²)**
- Momento: **N·mm**

Las conversiones se realizan **solo en las fronteras** (UI, importación, exportación), donde es habitual trabajar en kN y kN·m. `CalcStep.unit` transporta la etiqueta legible para los informes. La convención se documenta en `domain/units.py` con las constantes de conversión necesarias.

## Alternativas consideradas

- **`pint.Quantity`.** Ofrece seguridad en runtime y conversión automática, pero su tipado estático es débil (choca con Pyright `strict`) y añade sobrecoste en bucles de análisis numérico.
- **Value objects dimensionales** (`Moment`, `Force`, `Stress` con aritmética propia). Es la opción más segura en tipos, pero multiplica el código y la fricción en los motores numéricos; desproporcionado para el tamaño inicial del proyecto.
- **NewTypes por magnitud** (`kNm = NewType("kNm", float)`). Sin coste en runtime y con cierta seguridad estática, pero la aritmética entre tipos se degrada y ensucia el código.
- **Convención fija + conversión en fronteras (elegida).**

## Consecuencias

- Simplicidad y rendimiento; los motores operan con `float`.
- El riesgo de mezclar unidades se mitiga con la convención documentada, nombres de campo explícitos y etiquetas en la traza.
- Si en el futuro aparecen errores de unidades recurrentes, se puede introducir `NewType` **solo en los puntos calientes** sin alterar la arquitectura.

## Notas de implementación

Decisión de bajo coste y reversible. No afecta a los contratos centrales; es un detalle de representación que podría endurecerse más adelante si la práctica lo justifica.
