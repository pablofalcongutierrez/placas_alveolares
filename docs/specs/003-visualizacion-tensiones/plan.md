# Plan técnico — Milestone 003

```text
ModeloEstructural + HistorialSeccion + ProveedorLeyes
                         │
                         ▼
       construir_evolucion_alineada(...)
        ├── sistema_referencia_alineado()
        ├── preparar_componentes()
        ├── geometria_efectiva()
        ├── evaluar_tension()
        └── perfiles verticales + DTO
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
          PySide       Web/JSON    Matplotlib
```

## Archivos

- `domain/mechanics/alineacion_deformaciones.py`: sistema alineado, línea
  neutra y transformaciones.
- `domain/mechanics/campo_tensiones.py`: evaluación constitutiva por fibra.
- `application/dtos/visualizacion_tensiones.py`: contrato portable.
- `application/use_cases/visualizar_tensiones.py`: proyección del historial.
- `application/errores.py`: `VisualizacionInvalida`.
- `notebooks/ejemplo_2_visualizacion_tensiones.ipynb`: adaptador de
  demostración con Matplotlib.
- `tests/unit/domain/test_alineacion_deformaciones.py`: rotación e invariantes.
- `tests/unit/domain/test_campo_tensiones.py`: plano constitutivo y tensión.
- `tests/integration/test_visualizacion_tensiones.py`: pipeline completo, fases,
  huecos y cordones enfundados.

## Decisiones de diseño

- El dominio calcula la geometría mecánica; no se introducen colores ni
  conceptos de UI.
- La aplicación no importa `norms`; recibe el proveedor de leyes ya inyectado.
- El DTO contiene magnitudes físicas y usa `StrEnum` para vocabularios cerrados.
- Los perfiles se extraen de la malla efectiva ya existente; no se crea un
  segundo mallado.
- Los huecos se detectan por pertenencia a los triángulos, sin lógica especial
  por material.
- El renderizador del cuaderno es desechable; el contrato es el activo
  reutilizable.
