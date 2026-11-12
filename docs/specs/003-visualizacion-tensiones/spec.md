# Milestone 003 — Visualización alineada de deformaciones y tensiones

## Objetivo

Proporcionar un modelo de visualización independiente de la interfaz que
represente, por fase, la sección girada con la línea neutra horizontal, el plano
de deformaciones y los perfiles de tensión de cada material.

## Alcance

Incluye:

- sistema de referencia alineado con la línea neutra del plano común;
- evaluación de la deformación constitutiva y la tensión por fibra;
- geometría efectiva transformada, con huecos y componentes embebidos;
- perfiles verticales por componente, interrumpidos en huecos;
- distinción entre componentes adheridos y enfundados;
- metadatos de fase, tiempo, equilibrio y giro;
- DTO portable con rangos físicos por fase y globales;
- cuaderno de demostración que dibuja el contrato con Matplotlib.

No incluye:

- resolución de equilibrio desde la visualización;
- nuevos criterios normativos;
- interpolación temporal continua dentro de una fase;
- serialización JSON ni API HTTP;
- widget definitivo de PySide;
- mapas 2D o envolventes biaxiales completas.

## Criterios de aceptación

- `pyright` limpio en modo strict y `pytest` verde.
- La transformación alineada conserva la deformación de cada punto.
- La línea neutra queda en `v = 0` cuando la curvatura no es despreciable.
- Una curvatura nula conserva la orientación y marca la ausencia de línea
  neutra.
- Las tensiones usan el plano constitutivo de cada componente.
- Los cordones enfundados muestran su tensión propia y su condición.
- Los huecos del hormigón interrumpen el perfil y no se cuenta dos veces el
  acero.
- El contrato puede consumirse sin importar Qt, Matplotlib ni `norms`.
- El cuaderno ejecuta el pipeline completo y contiene las figuras embebidas.
