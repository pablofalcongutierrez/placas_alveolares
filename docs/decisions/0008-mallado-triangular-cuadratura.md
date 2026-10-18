# ADR 0008 — Mallado triangular con librería externa y cuadratura abstracta

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0007](0007-modelo-seccion-componentes-fases-adherencia.md)

## Contexto

Las propiedades seccionales (área, momento estático, inercia) y, en el futuro,
la integración de tensiones sobre la sección requieren **discretizar regiones**
delimitadas por contornos con huecos (placas alveolares, cordones circulares,
cavidades). Hay que decidir:

- cómo se discretiza la geometría (qué elementos) y cómo se calculan las
  integrales;
- si el mallado se implementa en el proyecto o se delega en una librería.

El mallado no es el objeto del TFM: es una pieza instrumental, un problema ya
resuelto, y el esfuerzo debe concentrarse en la mecánica y las normas.

## Decisión

### Mallado en triángulos con `mapbox-earcut`

- La región se **triangula** (triángulos, no otros polígonos) con
  [`mapbox-earcut`](https://pypi.org/project/mapbox-earcut/), que resuelve
  polígonos con huecos mediante anillos.
- El adaptador vive en `domain/mechanics/mallado.py`. La librería y `numpy`
  quedan **confinados** en ese módulo: la API pública devuelve
  `Triangulo` (tipo del dominio) y no filtra `numpy` al resto del núcleo.
- Se valida la contención de los huecos en el contorno exterior (un hueco
  fuera del contorno deja de triangulares sin aviso); el solape entre huecos no
  se valida.

### Cuadratura abstracta, regla de Gauss por defecto

- La integración se hace con **cuadratura de Gauss sobre cada triángulo**,
  definida mediante el protocolo `ReglaCuadratura` (`domain/mechanics/integracion.py`).
- Reglas incluidas: `Regla1Punto` (baricentro, exacta grado ≤ 1) y
  `Regla3Puntos` (Gauss de tres puntos, exacta grado ≤ 2). La regla por defecto
  es la de **tres puntos**, de modo que área, centro de gravedad e inercia son
  exactos para contornos poligonales.
- El integrador recibe un campo `Callable[[Punto], float]`, de modo que el
  mismo motor servirá para integrar tensiones cuando llegue el solver general.
- La calidad de los triángulos es irrelevante para integrar polinomios: la
  regla es exacta para su grado sea cual sea la forma del triángulo.

## Alternativas consideradas

- **Implementar la triangulación en el proyecto** (p. ej. *ear clipping*).
  Rechazada: no es el objeto del trabajo, añade código y pruebas de un problema
  resuelto, y las formas con huecos requieren técnicas específicas.
- **`triangle` (binding de Shewchuk).** Rechazada como primera opción: rueda
  ~5 veces mayor, sin sdist en la última versión, licencia LGPL-3.0 (relevante
  al distribuir la app) y mantenimiento esporádico. Se reserva si algún día se
  necesita mallado de calidad (refinado, ángulos mínimos) para integración de
  tensiones no lineales.
- **Fórmulas analíticas (shoelace) y sin mallado.** Rechazada: válidas para
  propiedades, pero no preparan el terreno para integrar tensiones sobre la
  sección; obligarían a rehacer el motor cuando llegue el solver.
- **Cuadratura fija (sin protocolo).** Rechazada: impide cambiar la regla
  (precisión frente a coste) y complica las pruebas de convergencia.

## Consecuencias

- Se añaden las dependencias `numpy` y `mapbox-earcut` (rueda `cp312` para
  Windows, licencia ISC, única dependencia `numpy`).
- `propiedades_seccion.propiedades_geometricas` calcula por mallado + Gauss y
  admite la regla como parámetro.
- Los cordones de pretensado se representan como contornos circulares
  poligonizados (`geometria.circulo`), sin tipos geométricos especiales.
- El error de poligonización del círculo (≈ 2,5 % en área con 16 puntos) es
  independiente del error de integración, que es nulo para el grado cubierto.
- Integrar tensiones en el solver futuro consiste en cambiar el campo, no el
  motor.

## Notas de implementación

- `mallado.py` desactiva localmente las comprobaciones de Pyright sobre la
  librería (no publica tipos); está justificado y acotado a ese módulo.
- Pruebas: `tests/unit/domain/test_mallado.py` y `test_integracion.py`.
