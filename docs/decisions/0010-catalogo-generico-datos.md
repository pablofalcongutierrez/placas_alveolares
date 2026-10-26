# ADR 0010 — Catálogo genérico de datos normativos y de usuario

- **Estado:** aceptado
- **Fecha:** 2026-10-24
- **Actualizado:** 2026-10-26
- **Relacionado:** [0001](0001-frontera-mecanica-fisica-vs-normativa.md), [0003](0003-catalogo-plugins-sin-switch-central.md), [0006](0006-familia-eurocodigo-parametros-nacionales.md), [0009](0009-errores-tipados-por-capas.md)

## Contexto

La aplicación incorpora progresivamente tablas de datos procedentes de distintas normas: aceros pasivos de la Tabla 34.2.a del Código Estructural, clases de hormigón, cordones de pretensado, juegos de coeficientes parciales y futuras tablas de durabilidad, cargas, geometrías normalizadas u otros parámetros. El mecanismo no debe quedar cerrado a materiales ni a coeficientes.

Se necesita una biblioteca común que permita:

- Elegir entre valores **normativos**, que no pueden modificarse ni eliminarse.
- Añadir datos de usuario con la misma forma tipada que los presets, **sin modificar el CRUD del catálogo**.
- Mantener varias normas en la misma biblioteca aunque compartan designaciones como `"B 500 S"`.
- Incorporar nuevos tipos de tablas sin crear un puerto y una implementación CRUD específicos para cada uno.

El alcance de extensibilidad son datos **tipados y definidos en código**. No se incluye un metamodelo para que el usuario final defina tablas y campos arbitrarios desde la UI.

Este ADR se refiere a los catálogos de **datos**. El catálogo de comprobaciones, que resuelve `(NormId, CheckKind)`, es una decisión distinta ([ADR 0003](0003-catalogo-plugins-sin-switch-central.md)).

## Decisión

### Un contrato genérico por tipo de dato

El puerto es un único `Catalogo[T]` (`application/ports/catalogo.py`):

- Cada instancia contiene **un solo tipo de dato**; no existe un catálogo heterogéneo con `object` ni con diccionarios genéricos.
- `T` es invariante porque aparece tanto en la consulta como en el registro.
- El contrato ofrece `listar`, `listar_disponibles`, `obtener`, `registrar` y `eliminar`.
- `AlmacenCatalogo[T]` (`application/almacen_catalogo.py`) es la implementación en memoria y declara explícitamente que cumple el puerto.

Añadir un tipo de tabla no requiere un nuevo puerto ni un nuevo CRUD. Se reutiliza `Catalogo[NuevoTipo]` y `AlmacenCatalogo[NuevoTipo]`.

### Fuentes de datos

- Los **presets normativos** viven en `norms/<norma>/` como tablas abiertas. Una tabla puede contener valores directos (`float`), registros normativos intermedios o tipos del dominio. La composición los convierte en el tipo `T` definitivo mediante las factorías de la norma.
- Las **entradas de usuario** se almacenan en una colección separada y mutable. La implementación actual vive en memoria; la persistencia SQLAlchemy y la UI son milestones posteriores.
- `application` no importa `norms`. Solo el composition root conoce las tablas y factorías concretas y construye los presets.

### Identidad y procedencia

Cada entrada es una `EntradaCatalogo[T]` con:

- `nombre`: designación visible;
- `origen`: `NORMATIVO` o `USUARIO`;
- `valor`: dato tipado;
- `norma`: `NormId` para presets y `None` para datos de usuario;
- `edicion` y `referencia`: metadatos opcionales de procedencia.

La identidad de un preset es `(NormId, nombre)`. Dos normas pueden compartir nombre sin sobrescribirse. Las entradas de usuario son independientes de la norma y aparecen en `listar_disponibles(norma)` junto con los presets de esa norma.

`edicion` y `referencia` son metadatos, no parte de la clave. Se asume una única edición activa por norma. `NormId` sigue siendo un vocabulario cerrado: añadir una norma exige un nuevo miembro, pero no modifica el catálogo.

Los datos de usuario no pueden reutilizar ningún nombre normativo, aunque el preset pertenezca a otra norma. Si se necesita una variante, se crea con otro nombre.

### Invarianza de los presets y errores

Los presets se guardan en una colección privada separada de las entradas de usuario:

- `listar` devuelve primero los presets normativos y después los datos de usuario.
- `registrar` y `eliminar` solo actúan sobre el espacio de usuario.
- Reutilizar un nombre normativo lanza `EntradaProtegida`.
- Dos presets con la misma norma y nombre lanzan `EntradaDuplicada` al construir el almacén.
- Nombres vacíos o metadatos incoherentes lanzan `EntradaCatalogoInvalida`.

Se espera que `T` sea inmutable, siguiendo la convención de dataclasses `frozen` y `slots`, para preservar la invarianza lógica de los presets.

### Composición y extensión

El composition root (`main.py`) deberá materializar los presets como `EntradaCatalogo[T]` e inyectarlos en los almacenes. La composición es el único punto que conecta `norms` con `application`.

Las consecuencias de extensión son:

- **Añadir una entrada:** cambiar solo los datos de la tabla normativa.
- **Añadir un tipo de tabla:** definir su dataclass de dominio, su tabla o factoría normativa y conectarlo en la composición; no se crea otro CRUD.
- **Añadir una norma:** añadir su `NormId`, sus presets y su registro en la composición.

## Alternativas consideradas

- **Una fachada CRUD por tipo (`CatalogoMateriales`, `CatalogoCoeficientes`, …).** Rechazada: duplica la misma lógica y vuelve a cerrar la extensión. Fue la implementación inicial y se retiró.
- **Un catálogo independiente por norma.** Rechazada: obliga a gestionar una instancia por combinación de norma y tipo, complica la biblioteca común de usuario y las comparaciones entre normas.
- **Identificar presets solo por nombre, con prefijos como `CE — B 500 S`.** Rechazada: la procedencia queda dentro de un texto, no permite filtrar de forma tipada y puede migrarse mal al persistir.
- **Un registro heterogéneo `Catalogo[object]` o basado en diccionarios.** Rechazada: pierde el tipado estricto, permite mezclar tipos y traslada errores a tiempo de ejecución.
- **Esquemas y tablas definidos por el usuario desde la UI.** Diferida y fuera del alcance actual: exigiría un metamodelo, validación dinámica y una capa de adaptación hacia los tipos tipados que consumen los cálculos.
- **Tablas en JSON/TOML externo.** Rechazada: los datos normativos dejarían de estar verificados por Pyright y se añadiría una capa de carga sin beneficio para el alcance actual.
- **Todos los presets sembrados como filas en la base de datos.** Rechazada: duplica el dato normativo, exige migraciones cuando cambia la norma y complica distinguir qué fila es editable. La base de datos guardará solo entradas de usuario.

## Consecuencias

- Un nuevo tipo de dato reutiliza el mismo puerto y la misma implementación; el coste está en definir el tipo y conectarlo, no en repetir CRUD.
- Añadir una entrada normativa sigue siendo un cambio de datos.
- La UI puede distinguir presets y datos de usuario mediante `EntradaCatalogo.origen`, y filtrar por `NormId`.
- `application` y `domain` no conocen normas concretas.
- Los nombres no están garantizados por tipos: las factorías normativas lanzan `CasoFueraDeAlcance` y el catálogo devuelve `None` para claves desconocidas.
- La base de datos solo contendrá entradas de usuario, lo que simplifica migraciones y evita duplicar el articulado.
- El catálogo común permite comparar presets de varias normas y compartir una única biblioteca de usuario.

## Estado de implementación

Implementado:

- `NormId` en `domain/checking/kinds.py`.
- `Catalogo[T]`, `EntradaCatalogo[T]` y `AlmacenCatalogo[T]`.
- `EntradaProtegida`, `EntradaCatalogoInvalida` y `EntradaDuplicada`.
- Pruebas unitarias del contrato genérico en `tests/unit/application/test_almacen_catalogo.py`.
- Tablas CE de aceros pasivos, hormigones, pretensados y coeficientes. El acero pasivo se limita actualmente a suministro en barra.

Pendiente:

- `construir_catalogos()` y la inyección de presets CE en `main.py`.
- Pruebas de integración de la composición real.
- Implementación SQLAlchemy de las entradas de usuario.
- Selectores y formularios de la UI.

## Notas de implementación

- Puertos: `application/ports/catalogo.py` y `application/ports/entradas_catalogo.py`.
- Implementación actual: `application/almacen_catalogo.py`.
- Errores: `application/errores.py`.
- Presets iniciales del CE: aceros B 400 S/500 S/400 SD/500 SD en barra, hormigones HA-25 a HA-60, cordones Y 1670/1770/1860/1960 S7 y coeficientes persistente/transitoria (1,5/1,15) y accidental (1,3/1,0).
