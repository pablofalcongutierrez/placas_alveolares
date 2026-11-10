# Milestone 002 — Estados seccionales, fases y transferencia de pretensado

## Objetivo

Incorporar un análisis seccional trazable por fases: estado global de
deformaciones, operaciones de tesado y pérdidas, adherencia progresiva,
acciones totales por fase y superposición geométrica de componentes embebidos.

## Alcance

Incluye:

- `EstadoSeccionFase` e `HistorialSeccion`.
- Fases instantáneas o con duración en días u horas.
- Acciones totales por fase.
- Operaciones abiertas: deformación impuesta, pretensado, pérdida y adherencia.
- Pretensado por fuerza, tensión o plano.
- Leyes constitutivas preparadas por fase.
- Huecos geométricos reales para acero embebido en hormigón.
- Solver con estado global y arranque desde el plano anterior.

No incluye:

- Cálculo normativo de relajación, fluencia o retracción.
- Pérdidas automáticas o evolución temporal constitutiva.
- Desadherencia o adherencia repetida.
- Booleanas generales para solapes parciales.
- Persistencia en base de datos.

## Criterios de aceptación

- `pyright` limpio en modo strict y `pytest` verde.
- La secuencia tesado → pérdida → transferencia conserva tres estados.
- La transferencia con cordón embebido malla el hueco del hormigón.
- No se cuenta dos veces el área del acero.
- Las fases sin equilibrio no admiten acciones.
- El historial permite reconstruir plano, referencias y resumen numérico.
- Añadir una operación no requiere modificar el bucle de fases.
