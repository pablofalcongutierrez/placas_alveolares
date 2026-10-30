# 0011 — Solvers no lineales y de continuación desacoplados de la física

## Contexto

El núcleo necesita resolver sistemas no lineales procedentes de la mecánica
seccional (equilibrio de deformaciones, momento-curvatura, evolución temporal)
y, más adelante, recorrer trayectorias de equilibrio con métodos de
continuación. Los candidatos previstos son:

- Newton, Newton modificado, Newton amortiguado con búsqueda de línea de
  Armijo y Broyden para ecuaciones ``F(x) = 0``;
- arc-length (longitud de arco) para trayectorias ``F(u, λ) = 0``.

Estos métodos no comparten la misma firma. En particular, arc-length **no** es
un solver de ``F(x) = 0`` con una incógnita adicional: el factor de carga
``λ`` es una incógnita del problema, se añade una restricción de camino y el
resultado es una secuencia de estados de equilibrio, no un único punto.

Las alternativas de librerías externas se evaluaron antes de implementar:

- **SciPy** no ofrece un Newton puro para sistemas: `root` incluye `hybr`
  (Powell híbrido), Broyden, `lm`, etc., pero no un Newton-Raphson clásico con
  historial de iteraciones. Tampoco incorpora arc-length.
- **JAX/optimistix**, **CasADi** y **PETSc/SNES** añaden dependencias grandes
  o imponen un ecosistema concreto para un problema de dimensión pequeña.
- **SymPy/mpmath** solo cubren bien casos escalares o sistemas muy pequeños.

## Decisión

### 1. Ubicación

Los métodos numéricos viven en `domain/numerics/`, no en `domain/mechanics/`.
No conocen física, normas ni la capa de aplicación; solo dependen de NumPy y
de `domain/errores.py`. Esto permite reutilizarlos en cualquier motor
mecánico y probarlos con sistemas matemáticos puros.

### 2. Dos familias de contratos

| Familia | Contrato | Problema | Resultado |
|---|---|---|---|
| Ecuaciones no lineales | `SolverNoLineal` | `F(x) = 0` | `ResultadoSolver` |
| Continuación | `SolverContinuacion` | `F(u, λ) = 0` + restricción | `ResultadoContinuacion` |

Cada solver concreto es una clase independiente que implementa su contrato.
La configuración se inyecta en el constructor de la implementación.

### 3. Problema parametrizado

`ProblemaParametrizado` representa ``F(u, λ) = 0`` y conserva:

- `residuo(u, λ)`;
- `jacobiano(u, λ) = ∂F/∂u`;
- `derivada_parametro(u, λ) = ∂F/∂λ`.

El método `con_parametro(λ)` devuelve un `ProblemaNoLineal` con el parámetro
fijo, de modo que Newton puede resolver cargas puntuales sin conocer la
continuación.

### 4. Newton y álgebra lineal

`Newton` implementa el bucle clásico:

```text
J(x)·Δx = −F(x)
x ← x + Δx
```

La resolución del sistema lineal se delega en `numpy.linalg.solve` (LAPACK);
no se reimplementa álgebra lineal. Si el problema no aporta Jacobiano, se
aproxima por diferencias finitas hacia adelante. La convergencia combina una
tolerancia absoluta y otra relativa al residuo inicial. El historial de
iteraciones queda en el resultado para que capas superiores puedan construir
la traza sin acoplar el solver a `CalcStep`.

### 5. Arc-length como continuación

El corrector de cada paso resuelve el sistema aumentado:

```text
x = (u, λ)

G(x) = [ F(u, λ) ] = 0
       [ c(u, λ) ]

J_G = [ ∂F/∂u    ∂F/∂λ ]
      [ ∂c/∂u    ∂c/∂λ ]
```

Con restricción esférica:

```text
c(u, λ) = ‖u − u_previo‖² + ψ²(λ − λ_previo)² − Δs²
```

y con restricción cilíndrica:

```text
c(u, λ) = ‖u − u_previo‖² − Δs²
```

El contrato `RestriccionArco` define `residuo` y `jacobiano` (la pareja
`(∂c/∂u, ∂c/∂λ)`). Se incluyen `ArcoEsferico` y `ArcoCilindrico` como
implementaciones puras y testeables.

El futuro `ArcoLongitud` implementará `SolverContinuacion` y recibirá un
`SolverNoLineal` como corrector. De este modo, Newton, Newton modificado,
Newton amortiguado o Broyden pueden reutilizarse sin duplicar el algoritmo de
continuación.

## Alternativas descartadas

- **Meter `λ` dentro de `x` y usar `SolverNoLineal` para todo.** Se pierde la
  semántica del parámetro, no se puede describir la restricción de arco y el
  resultado deja de ser una trayectoria. Además, el predictor y el control del
  paso no encajan en la firma `resolver(problema, x0)`.
- **Un único `Solver` genérico con tipos de problema y resultado variables.**
  Añade abstracción sin uso real y dificulta la lectura de los contratos.
- **Envolver SciPy.** No aporta un Newton puro para sistemas ni arc-length, y
  oculta el historial de iteraciones necesario para la traza.
- **Ubicar los solvers en `domain/mechanics/`.** Los acopla innecesariamente a
  la mecánica y dificulta su reutilización en otros cálculos.

## Consecuencias

- Añadir un solver de ecuación nuevo consiste en implementar
  `SolverNoLineal`; no se modifica Newton ni los llamadores.
- Añadir arc-length consiste en implementar `SolverContinuacion` y reutilizar
  un corrector existente.
- El paquete no depende de normas ni de aplicación; la regla de dependencias
  se mantiene.
- El coste es mantener dos contratos y una noción explícita de estado
  parametrizado, pero evita una ruptura de API cuando se incorpore
  continuación.
- La implementación concreta de arc-length, la estrategia adaptativa de paso,
  Newton modificado, Newton amortiguado y Broyden quedan para milestones
  posteriores.

## Vínculo con la implementación

- `domain/numerics/base.py` — `SolverNoLineal`.
- `domain/numerics/problema.py` — `ProblemaNoLineal` y
  `ProblemaParametrizado`.
- `domain/numerics/newton.py` — `Newton`.
- `domain/numerics/diferencias_finitas.py` — Jacobiano numérico reutilizable.
- `domain/numerics/continuacion/` — contratos, restricciones y tipos de
  trayectoria.
- `tests/unit/domain/numerics/` — pruebas de convergencia, errores,
  parametrización y restricciones de arco.
