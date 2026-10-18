# Bases de cálculo — Milestone 001

> Fundamentos teóricos del milestone, **aislados de la implementación** para poder reutilizarse
> en la memoria del TFM. Cada apartado termina con un breve *Vínculo con la implementación*
> que enlaza el concepto con los tipos y documentos del proyecto.
>
> Documentos relacionados: [`spec.md`](spec.md) · [`plan.md`](plan.md) · [`tasks.md`](tasks.md)

## 1. Hipótesis cinemática: sección plana (Bernoulli–Navier)

La teoría de flexión de vigas esbeltas descansa en la hipótesis de **Navier–Bernoulli**: las
secciones transversales, inicialmente planas y perpendiculares al eje de la pieza, permanecen
planas tras la deformación. Esto equivale a suponer que la distribución de **deformaciones
longitudinales** sobre la sección es lineal.

En un sistema de ejes generales, la deformación longitudinal de una fibra situada en la posición
`(y, z)` de la sección transversal puede escribirse como:

```
ε(x, y, z) = ε₀(x) + κ_y(x)·z − κ_z(x)·y
```

donde:

- `ε₀(x)`: deformación del eje de la pieza.
- `κ_y(x)`, `κ_z(x)`: curvaturas alrededor de los ejes `y` y `z` respectivamente.
- `(x, y, z)`: coordenadas de la fibra considerada.

Para **flexión simple** en el plano `y-z` alrededor del eje `y`, la expresión se reduce a:

```
ε(z) = ε_c + κ·(z − z_c)
```

siendo:

- `ε(z)`: deformación longitudinal en la fibra de cota `z`.
- `ε_c`: deformación en el eje neutro (cota `z_c`).
- `κ`: curvatura de la sección en el plano `y-z`.

La hipótesis de sección plana garantiza la **compatibilidad de deformaciones** entre el hormigón
y las armaduras: cada capa de refuerzo adopta la deformación de la fibra de hormigón situada a su
misma cota, lo que se traduce en **adherencia perfecta** entre ambos materiales (caso de hormigón
armado). En el caso de pretensado, la compatibilidad se planteará considerando la deformación
inicial del acero de pretensado y su evolución conjunta con el hormigón.

Esta hipótesis es válida para piezas esbeltas sometidas a flexión y a compresión o tracción
compuesta. No es aplicable sin correcciones adicionales en zonas fuertemente perturbadas por
cortante, en vigas de gran canto ni en zonas de apoyo directo, donde la deformación por cortante
no es despreciable.

### Vínculo con la implementación

- El plano de deformaciones `ε(z)` se representará mediante un *strain profile* en `domain/state/`
  cuando se incorpore el solver general por fibras (milestone posterior).
- En este milestone, la compatibilidad se materializa a través del **diagrama de deformaciones del
  bloque rectangular** empleado por la comprobación de flexión
  (`run_flexure`, ver [`plan.md`](plan.md#norma-eurocódigo)).
- Las leyes tensión-deformación de cada material se desacoplan tras el protocolo `StressStrainLaw`
  (`domain/mechanics/laws.py`); ver [ADR 0001](../../decisions/0001-frontera-mecanica-fisica-vs-normativa.md).

## 2. Sistema de ejes y convención de signos

### 2.1. Ejes de la sección

Se adopta un sistema de ejes cartesianos ortogonales ligado a la sección transversal de la pieza:

- **Eje `x`**: longitudinal de la pieza, positivo en el sentido del eje de la barra.
- **Eje `y`**: horizontal en el plano de la sección, positivo hacia la derecha.
- **Eje `z`**: vertical en el plano de la sección, positivo hacia arriba.

El origen `O` se sitúa en el **centro de gravedad de la sección bruta** de hormigón. Todas las
propiedades geométricas (área, momentos estáticos, momentos de inercia) se definen respecto a este
sistema de referencia.

![Figura 1: ejes de la sección en el plano y-z](../../../resources/images/specs/001/ejes_seccion_2d.png)

*Figura 1. Sistema de ejes `y-z` en la sección transversal; origen en el centro de gravedad.*

![Figura 2: ejes locales de la pieza en tres dimensiones](../../../resources/images/specs/001/ejes_seccion_3d.png)

*Figura 2. Ejes locales de la pieza: `x` longitudinal, `y` y `z` en el plano de la sección.*

### 2.2. Convención de signos

- **Deformaciones**: positivas en tracción y negativas en compresión.
- **Curvatura `κ`**: positiva cuando produce tracción en las fibras inferiores (`z < 0`) y
  compresión en las superiores (`z > 0`); es decir, curvatura de concavidad hacia arriba
  (momento flector positivo según la convención habitual de flexión simple).
- **Tensiones normales `σ`**: positivas a tracción y negativas a compresión. Para una sección
  homogénea no fisurada sometida a flexión simple `My`, la distribución es lineal:

  ```
  σ(z) = −My · z / I_y
  ```

  de modo que un momento `My` positivo genera compresión en la fibra superior (`z > 0`) y tracción
  en la inferior (`z < 0`).
- **Canto útil `d`**: distancia desde la fibra extrema de compresión hasta el centro de gravedad
  de la armadura a tracción.

### Vínculo con la implementación

- El plano `y-z` y el sentido de los ejes se fijan en `domain/model/geometry.py`
  (ver [`plan.md`](plan.md#archivos-a-crear)).
- La magnitud `My` con su signo se transporta en `InternalForces(n, m_y)` (`domain/model/actions.py`).
- La convención de unidades asociada es mm / N / MPa / N·mm
  (ver [ADR 0004](../../decisions/0004-unidades-convencion-n-mm-mpa.md) y `domain/units.py`).

## 3. Leyes constitutivas y bloque rectangular

Las tensiones se obtienen a partir de las deformaciones mediante las **leyes constitutivas** de cada
material: un diagrama tensión-deformación del hormigón y otro del acero. En el análisis en rotura
(ELU) se emplea la simplificación del **bloque rectangular de tensiones**, que sustituye el
diagrama parabólico por una distribución uniforme `η·fcd` sobre una profundidad `λ·x`:

```
C = η · fcd · b · (λ · x)          (resultante de compresión en el hormigón)
T = As · fyd                       (resultante de tracción en la armadura)
```

El equilibrio de resultantes `C = T` permite obtener la profundidad del bloque `x`, el brazo
mecánico `z = d − λ·x/2` y el momento resistido `MRd = As·fyd·z`. Para hormigones de clase no
superior a C50/60: `λ = 0,8` y `η = 1,0`.

### Vínculo con la implementación

- Los coeficientes (`γc`, `γs`, `λ`, `η`) y las referencias normativas residen en `EurocodeParams`
  y `ClauseRefs` (`norms/eurocode/params.py`); su justificación está en
  [ADR 0006](../../decisions/0006-familia-eurocodigo-parametros-nacionales.md).
- Las expresiones y el ejemplo numérico de validación están en
  [`spec.md`](spec.md#ejemplo-de-referencia-de-validación) y [`plan.md`](plan.md#norma-eurocódigo).

## 4. Relación tensión-deformación en el acero de armar

Se adopta un comportamiento elastoplástico perfecto para el acero de armar: lineal hasta el límite
elástico de cálculo `fyd = fyk/γs` y plástico a partir de él. La deformación del acero se limita por
su **deformación última** `εud` para garantizar ductilidad.

### Vínculo con la implementación

- La ley se expresará como una implementación del protocolo `StressStrainLaw`
  (`domain/mechanics/laws.py` y `domain/mechanics/generic_laws.py`).
- En el milestone 001, la armadura a tracción se supone plastificada (`σs = fyd`), coherente con el
  ejemplo de referencia.
