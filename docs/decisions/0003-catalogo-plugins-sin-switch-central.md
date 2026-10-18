# ADR 0003 — Catálogo de plugins para selección sin condicional central

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0002](0002-checks-funciones-puras-tipadas.md), [0006](0006-familia-eurocodigo-parametros-nacionales.md)

## Contexto

El usuario selecciona el tipo de cálculo y la normativa. No se quiere un bloque condicional central (`if norma == "ce": ... elif norma == "aci": ...`) que haya que actualizar con cada incorporación, ni que añadir un método obligue a tocar partes del sistema que no deberían depender de él. A la vez, hay que conservar el tipado de cada comprobación.

## Decisión

Un **catálogo** (`application/catalog.py`) registra **descriptores** de comprobaciones y las resuelve por clave compuesta `(NormId, CheckKind)`:

```python
@dataclass(frozen=True)
class CheckDescriptor:
    kind: CheckKind
    norm: NormId
    name: str
    applicability: Callable[[StructuralModel], tuple[ApplicabilityIssue, ...]]
    default_params: Callable[[], object]
    prepare_and_run: Callable[[StructuralModel, object], CheckResult]
    run_direct: Callable[[object, object], CheckResult]

class CheckCatalog:
    def register(self, d: CheckDescriptor) -> None: ...
    def resolve(self, norm: NormId, kind: CheckKind) -> CheckDescriptor | None: ...
    def available(self, norm: NormId | None = None) -> list[CheckDescriptor]: ...
```

Cada norma se declara en su `module.py` con `register(catalog)`. El **composition root** (`main.py`) es el único que importa los paquetes de normas y los registra. Los casos de uso solo conocen `NormId` y `CheckKind`, nunca las implementaciones.

## Alternativas consideradas

- **Condicional central por norma.** Rechazada: acoplamiento y modificación obligada con cada norma nueva.
- **Autodescubrimiento de paquetes (`pkgutil`/entry points).** Diferida: añade magia y dificulta la trazabilidad para un TFM unipersonal. Se empieza con imports explícitos en el composition root (una línea por norma); migrar a autodescubrimiento más adelante no rompe contratos.
- **Catálogo con descriptores (elegida).**

El descriptor encapsula la **heterogeneidad** de checks distintos bajo una superficie uniforme. El único punto de pérdida de tipado es el uso de `object` en el descriptor; es seguro por construcción porque una factoría genérica por norma garantiza la coherencia entrada/parámetro/resultado, y los tests llaman a `run` directamente con tipado completo.

## Consecuencias

- Añadir una norma = crear su paquete + **una línea** de registro en el composition root.
- La UI enumera lo disponible mediante `catalog.available()`, sin conocer normas.
- La comparación entre normas (`compare_norms`) es trivial: iterar las normas que ofrecen un `CheckKind`.
- El catálogo es un punto de "borrado de tipos" acotado y documentado; no se propaga al resto del sistema.

## Notas de implementación

Decisión esencial para el requisito de selección desacoplada. El estilo de registro (explícito vs. autodescubrimiento) es un detalle reversible.
