# 0013 — Superposición geométrica explícita de componentes

- **Estado:** aceptado
- **Fecha:** 2026-11-09
- **Relacionado:** [0007](0007-modelo-seccion-componentes-fases-adherencia.md), [0008](0008-mallado-triangular-cuadratura.md)

## Contexto

El ADR 0007 preveía descontar el hormigón desplazado por un cordón mediante una
corrección tensional `(σ_s − σ_c,host)·A_s`. Para el cálculo por fibras se
prefiere que la geometría represente directamente la materia existente y que
no haya áreas contadas dos veces.

## Decisión

- Cada componente embebido de acero declara `componente_anfitrion_id`.
- El anfitrión debe ser un componente de hormigón y debe contener
  geométricamente al componente embebido.
- Al preparar la fase, los contornos exteriores de los componentes embebidos
  activos se añaden como huecos del anfitrión.
- El anfitrión se malla con esos huecos mediante la triangulación existente.
- El acero se malla por separado con su geometría completa.
- Los solapes parciales no declarados, los anfitriones inexistentes y los
  huecos solapados producen errores de validación.
- El contacto de bordes sin área común no se considera solape.

## Alternativas descartadas

- Corrección tensional equivalente: mantiene la geometría duplicada y separa
  el resultado geométrico del resultado tensional.
- Booleanas poligonales generales: amplían innecesariamente las dependencias y
  el alcance; los solapes no resueltos se rechazan explícitamente.
- Detección automática de anfitrión: es ambigua con varias capas de hormigón.

## Consecuencias

- El área neta y las inercias del hormigón son correctas sin factores de
  homogeneización.
- Los cordones no adheridos también desplazan hormigón, aunque su tensión no
  se integre en el plano común.
- El modelo exige declarar explícitamente la relación de embebido.
