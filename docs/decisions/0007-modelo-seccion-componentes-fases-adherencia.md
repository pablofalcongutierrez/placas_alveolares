# ADR 0007 — Modelo de sección por componentes, fases y adherencia

- **Estado:** aceptado
- **Fecha:** 2026-10-18
- **Relacionado:** [0001](0001-frontera-mecanica-fisica-vs-normativa.md), [0004](0004-unidades-convencion-n-mm-mpa.md), [0008](0008-mallado-triangular-cuadratura.md)

## Contexto

La sección transversal debe representar, sin perder generalidad, situaciones que aparecen en las placas alveolares y en estructuras pretensadas:

- **Fases de construcción**: la placa prefabricada existe sola en una fase inicial y, tras hormigonar la capa de compresión, forma una sección compuesta en la fase final. También puede entrar armadura o refuerzo en fases posteriores.
- **Enfundado de cordones**: un cordón enfundado existe físicamente en la sección pero no transmite pretensado al hormigón en esa posición.
- **Materiales distintos coexistiendo**: capa de compresión de clase distinta a la placa; cordones frente a armadura pasiva.

Hay que decidir cómo se modela la **activación** de componentes, si un componente pertenece a una fase o es independiente de ella, y cómo se trata la superposición de geometrías (un cordón ocupa un área donde también se ha definido hormigón).

La decisión no debe romper la frontera del [ADR 0001](0001-frontera-mecanica-fisica-vs-normativa.md): los materiales contienen propiedades físicas, y las leyes constitutivas son normativas y se inyectan por el preparador.

## Decisión

### La sección es un conjunto de componentes independientes y superpuestos

- Una `Seccion` es la definición **completa e inmutable** de todos los componentes que llegarán a existir. No hay una sección distinta por fase.
- Cada `ComponenteSeccion` aporta su propia **geometría** (`GeometriaContorno`: contorno exterior con huecos) y su **material** (`Hormigon`, `AceroArmadura`, `AceroPretensado`). No hay tipos geométricos especiales para armaduras: un cordón se representa como un **contorno circular poligonizado** (`geometria.circulo`) y el mallado no necesita casos particulares.
- Los componentes **no conocen las fases**; solo anotan `fase_incorporacion` (cuándo entran en servicio). La activación es una **consulta pura**: `componentes_activos(seccion, fase)`. Comprobar otra fase se resuelve construyendo el modelo con otra `fase_activa`, sin mutar nada.

### Fase y adherencia son ejes ortogonales

- `fase_incorporacion` es el eje **temporal** (capa de compresión que llega después).
- `adherencia` (`CondicionAdherencia.ADHERIDO` / `ENFUNDADO`) es el eje de **adherencia** (cordón que existe pero no transmite).
- No se fusionan en un único booleano «activo»: responden a preguntas distintas y las normas los tratan de forma distinta.

### La superposición la resuelve el motor de integración, no la geometría

- Las geometrías son declarativas y pueden solaparse: el contorno circular de un cordón queda dentro del contorno de hormigón. La sección «ve» la superposición en el momento de integrar.
- Regla de superposición (se implementará en el motor de integración con el solver general por fibras):

  | Componente embebido (cordón) | Contribución |
  |---|---|
  | Adherido dentro de un contorno (hormigón anfitrión) | `(σ_s(ε) − σ_c,host(ε)) · A_s` |
  | Enfundado dentro de un contorno | `−σ_c,host(ε) · A_s` (efecto vaino, no transmite) |
  | Contorno sobre contorno | prohibido: los contornos se apilan (interfaz), no se solapan |

- Todos los componentes comparten el **mismo plano de deformaciones** `ε(z)` (adherencia perfecta en la interfaz).
- En consecuencia, **no hay homogeneización analítica** (factores `n`, sección transformada) en el dominio: la integración numérica por materiales resuelve la sección compuesta directamente. El caso elástico `(n − 1)` es solo la especialización de la regla anterior.

#### Por qué **no** se recorta el contorno del cordón

La sección se declara con componentes **superpuestos**: el contorno de hormigón cubre *todo* el área, **incluido el disco del cordón**. Un integrador ingenuo contaría ese disco **dos veces** (una como hormigón y otra como acero). La solución no es recortar geométricamente el círculo del contorno (lo que exigiría booleanos de polígonos, acoplaría el contorno a la posición de cada cordón y mezclaría huecos reales con huecos contables), sino corregir en el momento de integrar.

La contribución real del cordón es *lo que aporta el acero menos lo que habría aportado el hormigón que desplaza*, evaluada a la deformación `ε` del punto:

- `σ_s(ε)`: tensión del acero según su ley constitutiva.
- `σ_c,host(ε)`: tensión del hormigón **anfitrión** (el contorno que contiene al cordón) a esa misma `ε`.

**Adherido**: el cordón sigue el plano de deformaciones y trabaja a `σ_s(ε)`; como el hormigón ya contó ese disco a `σ_c,host(ε)`, se descuenta:

```
(σ_s(ε) − σ_c,host(ε)) · A_s     ≡     acero completo  −  hormigón desplazado
```

**Enfundado**: el cordón desliza dentro de la vaina y, desde el punto de vista de la sección, **no toma tensión** (`σ_s = 0`; su pretensado no se transmite en esa sección, el anclaje es asunto normativo del check), pero la vaina sí desplaza hormigón:

```
−σ_c,host(ε) · A_s     ≡     se comporta exactamente como un HUECO (vaino)
```

Es la misma fórmula con `σ_s = 0`.

**Ejemplo numérico** (elástico, sección sin fisurar). Hormigón C30 (`E_c = 33 000 MPa`), cordón de `A_s = 100 mm²` (`E_s = 195 000 MPa`) y deformación en su fibra `ε = 2‰`:

- `σ_c = 33 000 · 0,002 = 66 MPa`.
- **Adherido**: `σ_s = 195 000 · 0,002 = 390 MPa` → aporta `(390 − 66)·100 = 32 400 N` (equivale a `39 000 N` de acero menos `6 600 N` de hormigón desplazado).
- **Enfundado**: aporta `−66·100 = −6 600 N` (como si esos `100 mm²` de hormigón no existieran).

En régimen elástico `σ_s − σ_c = (E_s − E_c)·ε`, de modo que el cordón adherido equivale a `(n − 1)·A_s` de hormigón transformado: la corrección clásica de la sección homogeneizada es el caso elástico de esta regla.

### Proveedores afectados

- `domain/model/geometria.py`, `materiales.py`, `seccion.py`, `fases.py`, `acciones.py`, `modelo.py`.
- `domain/mechanics/mallado.py` (triangulación) e `integracion.py` (cuadratura) — véase [ADR 0008](0008-mallado-triangular-cuadratura.md).
- `domain/mechanics/propiedades_seccion.py` calcula propiedades sobre el mallado.

## Alternativas consideradas

- **Flag `active: bool` en el componente.** Rechazada: semántica ambigua (¿fase? ¿enfundado?), introduce estado mutable y no conserva el motivo de la desactivación.
- **Subclases por situación** (`ComponenteActivo`, `ComponenteEnfundado`…). Rechazada: explosión de tipos y polimorfismo sin datos.
- **Una `Seccion` distinta por fase.** Rechazada: duplica la definición (la placa prefabricada se repite en cada fase) y permite inconsistencias entre fases.
- **Tipos geométricos de área concentrada** (capa a una cota, punto con área). Rechazada: los cordones y la armadura se representan mejor como contornos circulares, lo que uniforma el modelo y el mallado en triángulos.
- **Mallar los cordones** (restar del contorno los círculos que ocupan). Rechazada: exige booleanos de polígonos, acopla el contorno a la posición de cada cordón y mezcla huecos reales (alveolos, vainos) con huecos contables. El mismo efecto se obtiene exactamente con la regla de superposición.
- **Homogeneización analítica de la sección compuesta.** Rechazada como mecanismo del dominio: con integración numérica es innecesaria y con varios hormigones resulta confusa. Se reserva, si acaso, al caso elástico como especialización de la regla de superposición.

## Consecuencias

- El dominio queda más simple: geometría declarativa superpuesta, sin operaciones booleanas.
- La corrección física por solape de materiales ocurre en un único punto, el motor de integración, en lugar de repartirse por fórmulas de homogeneización.
- La corrección por defecto es una única consulta de activación; comprobar otra fase no reconstruye el modelo.
- Los sistemas de unidades se fijan en `docs/decisions/0004-unidades-convencion-n-mm-mpa.md`.
- Los huecos reales (alveolos, vainos de postesado sin inyectar) se modelan como `huecos` de un contorno, sin recurrir a mallado.

## Notas de implementación

- `Seccion` exige al menos un componente; `ModeloEstructural` exige que `fase_activa` figure entre sus fases.
- El código nuevo de este dominio se escribe íntegramente en español (véase `AGENTS.md`).
