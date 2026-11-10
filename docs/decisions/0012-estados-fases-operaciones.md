# 0012 — Estados seccionales, fases temporales y operaciones

- **Estado:** aceptado
- **Fecha:** 2026-11-09
- **Relacionado:** [0007](0007-modelo-seccion-componentes-fases-adherencia.md), [0011](0011-solvers-no-lineales-desacoplados.md), [0013](0013-superposicion-geometrica-componentes.md)

## Contexto

La sección y sus componentes describen la geometría y los materiales, pero no
el estado deformacional de cada fase. Guardar el plano en `Seccion` mezclaría
definición y resultado; guardar únicamente `deformacion_inicial` en cada
componente de cálculo impide distinguir la deformación heredada de la
deformación impuesta por pretensado. Además, una fase puede solo actualizar
el estado —tesado o pérdidas— sin resolver todavía el equilibrio.

## Decisión

- `Seccion` y `Fase` son definiciones inmutables.
- `EstadoSeccionFase` contiene el plano común, los estados de los componentes
  activos y, si procede, un resumen de equilibrio.
- `HistorialSeccion` conserva la secuencia de estados.
- La deformación constitutiva de un componente adherido es
  `plano_comun − plano_referencia + deformacion_impuesta`.
- `plano_referencia` se fija al activar el componente y se actualiza al
  adherirlo. La transición de no adherido a adherido es única.
- Las fases tienen `tiempo_inicio` y `tiempo_fin`; las horas se convierten a
  días. Las fases instantáneas tienen ambos tiempos iguales.
- Las acciones son totales y viven en la fase. Una fase sin equilibrio no
  puede declarar acciones.
- Las operaciones implementan un protocolo abierto y se aplican al final de la
  fase, antes del equilibrio.
- El solver recibe el estado global y arranca desde el plano de la fase
  anterior.

## Alternativas descartadas

- Guardar el plano en `Seccion`: mezcla definición y resultado.
- Guardar solo un plano inicial por componente: pierde la distinción entre
  historia y pretensado.
- Una fase por cada operación con resolución obligatoria: no permite tesado o
  pérdidas sin equilibrio seccional.
- Un `if` central por tipo de operación: obliga a modificar el procesador al
  añadir operaciones.

## Consecuencias

- El análisis por fases es reproducible y cada estado puede auditarse.
- El motor mecánico sigue siendo independiente de la norma y del algoritmo
  numérico.
- La preparación de leyes puede variar por fase.
- La persistencia futura puede almacenar estados sin reconstruir fórmulas.
