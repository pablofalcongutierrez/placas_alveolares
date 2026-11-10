# Plan técnico — Milestone 002

La implementación sigue estas capas:

```text
Seccion + Fase + Operaciones
          │
          ▼
EstadoSeccionFase + HistorialSeccion
          │
          ▼
preparar_componentes (mallas efectivas + leyes por fase)
          │
          ▼
resolver_equilibrio_seccion (estado global + Newton inyectado)
          │
          ▼
analizar_fases (activación, operaciones, equilibrio, historial)
```

## Archivos principales

- `domain/model/tiempo.py`: `Tiempo`, `UnidadTiempo`.
- `domain/model/operaciones.py`: contrato y entradas de pretensado/pérdidas.
- `domain/model/seccion.py`: IDs y anfitrión geométrico.
- `domain/model/fases.py`: tiempos, acciones y operaciones.
- `domain/model/modelo.py`: validación de secuencia temporal.
- `domain/state/estado_seccion.py`: estado por componente y estado global.
- `domain/state/historial_seccion.py`: secuencia de estados.
- `domain/state/operaciones.py`: operaciones concretas.
- `domain/mechanics/geometria_efectiva.py`: huecos de componentes embebidos.
- `domain/mechanics/preparacion_componentes.py`: mallas y leyes por fase.
- `domain/mechanics/solver_deformaciones.py`: integración y equilibrio global.
- `domain/mechanics/analisis_fases.py`: orquestación e historial.

## Reglas de implementación

- Dataclasses `frozen=True, slots=True`.
- Sin diccionarios genéricos como contrato ni `**kwargs`.
- Las operaciones se aplican en orden y no mutan estados.
- La preparación de leyes no introduce normas en `domain`.
- La geometría efectiva se calcula por fase según los componentes activos.
