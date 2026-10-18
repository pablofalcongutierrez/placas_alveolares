# ADR 0009 — Errores tipados por capas, con raíz común en el dominio

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0001](0001-frontera-mecanica-fisica-vs-normativa.md), [0003](0003-catalogo-plugins-sin-switch-central.md), [0007](0007-modelo-seccion-componentes-fases-adherencia.md)

## Contexto

Hasta ahora el dominio rechazaba entradas inválidas con `ValueError` genéricos, sin distinguir el tipo de incumplimiento ni la capa que lo detecta. Esto plantea varios problemas:

- La presentación no puede traducir un error a un mensaje de usuario sin inspeccionar el texto.
- No se puede capturar de forma selectiva «todo lo que salga del dominio» frente a errores de aplicación, infraestructura o interfaz.
- Cada capa iba a inventar sus propias excepciones, con solapamientos y jerarquías incompatibles.

Se necesita una convención única, compatible con Pyright `strict`, que ordene los errores de **todas** las capas y no solo del dominio.

## Decisión

### Raíz única en el dominio

Todos los errores del sistema derivan de `ErrorDominio` (`domain/errores.py`), de modo que la presentación pueda capturar un único tipo raíz. El dominio distingue dos familias:

- `ErrorValidacion`: una entrada incumple una invariante del modelo. Se especializa por concepto: `GeometriaInvalida`, `MaterialInvalido`, `SeccionInvalida`, `FaseInvalida` y `ModeloInvalido`.
- `ErrorCalculo`: un motor numérico no puede completar su cálculo. Se especializa por motor; hoy `ErrorMallado`.

Las validaciones se ejecutan en la construcción de los objetos (dataclasses `frozen`), de forma que un objeto válido por tipos es también válido por invariantes.

### Extensión al resto de capas

La misma convención se aplica fuera del dominio. Cada capa define su propia base, que **hereda de `ErrorDominio`**:

| Capa | Base | Ejemplos previstos |
|---|---|---|
| dominio | `ErrorDominio` | `GeometriaInvalida`, `ModeloInvalido`, `ErrorCalculo` |
| normas | `ErrorNorma(ErrorDominio)` | parámetros o cláusulas no soportadas |
| aplicación | `ErrorAplicacion(ErrorDominio)` | `CheckNotAvailable`, `CheckNotApplicable`, fallo de caso de uso |
| infraestructura | `ErrorInfraestructura(ErrorDominio)` | persistencia, configuración, importación/exportación |
| presentación | `ErrorPresentacion(ErrorDominio)` | validación de formularios, fallos de controlador |

Así, cualquier consumidor externo puede capturar `ErrorDominio` para cubrir el sistema completo, o una base concreta para reaccionar a una capa. Los errores de tipado (campos obligatorios ausentes) siguen resolviéndose en tiempo de análisis con Pyright y **no** se convierten en excepciones.

## Alternativas consideradas

- **`ValueError` / `RuntimeError` genéricos.** Rechazada: obliga a inspeccionar mensajes, no permite captura selectiva y mezcla semánticas (validación, cálculo, persistencia) bajo el mismo tipo.
- **Una jerarquía independiente por capa.** Rechazada: impide capturar un error común de extremo a extremo y duplica conceptos.
- **Una única excepción con un `enum` de código.** Rechazada: pierde el tipado, obliga a comparar códigos y dificulta el manejo específico con `except`.
- **Errores de dominio heredando de `ValueError`.** Rechazada en favor de una jerarquía pura: mantener la compatibilidad con `except ValueError` perpetúa el problema y enturbia la semántica de las capas.
- **Raíz común fuera del dominio (p. ej. un paquete `common`).** Rechazada: introduce una dependencia transversal nueva; el dominio es la capa más interna y es el lugar natural del tipo raíz.

## Consecuencias

- Los consumidores capturan `ErrorDominio` o las bases de cada capa, sin depender de mensajes de texto.
- La jerarquía es parte del contrato público del núcleo; añadir un error especializado es un cambio aditivo.
- La validación de invariantes se concentra en la construcción de los objetos del dominio.
- `docs/architecture.md` refleja esta política en la tabla de gestión de errores.

## Notas de implementación

- Módulo raíz: `src/placas_alveolares/domain/errores.py`.
- Los errores se importan de forma explícita desde su módulo; no se reexportan en `domain/__init__.py`.
- Al implementar cada capa nueva se creará su módulo de errores con la base correspondiente heredando de `ErrorDominio`.
