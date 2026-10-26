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
ε(y, z) = ε₀ + κ_y·z − κ_z·y
```

donde:

- `ε₀`: deformación del eje de la pieza.
- `κ_y`, `κ_z`: curvaturas alrededor de los ejes `y` y `z` respectivamente.
- `(y, z)`: coordenadas de la fibra considerada.

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
- Las leyes tensión-deformación de cada material se desacoplan tras el protocolo `LeyTensionDeformacion`
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
- **Esfuerzo axil `N`**: positivo a tracción.
- **Curvatura `κ`**: positiva cuando produce tracción en las fibras inferiores (`z < 0`) y
  compresión en las superiores (`z > 0`); es decir, curvatura de concavidad hacia arriba
  (momento flector positivo según la convención habitual de flexión simple).
- **Momento `My`** (alrededor del eje horizontal): positivo cuando produce tracción en las
  fibras inferiores (`z < 0`).
- **Momento `Mz`** (alrededor del eje vertical): positivo cuando produce tracción en las fibras
  con `y > 0`.
- **Tensiones normales `σ`**: positivas a tracción y negativas a compresión. Para una sección
  homogénea no fisurada sometida a axil y flexión biaxial, con ejes principales de inercia
  (`I_yz = 0`), la distribución es lineal:

  ```
  σ(y, z) = N / A − My · z / I_y + Mz · y / I_z
  ```

  de modo que `My` positivo comprime la fibra superior (`z > 0`) y `Mz` positivo comprime el
  lado `y < 0`. Si los ejes no son principales (`I_yz ≠ 0`), los términos de flexión se acoplan
  y la expresión debe resolverse con la matriz de inercia completa.
- **Canto útil `d`**: distancia desde la fibra extrema de compresión hasta el centro de gravedad
  de la armadura a tracción.

### Vínculo con la implementación

- El plano `y-z` y el sentido de los ejes se fijan en `domain/model/geometria.py`
  (ver [`plan.md`](plan.md#archivos-a-crear)).
- Los esfuerzos con su signo se transportan en `EsfuerzosInternos(n, m_y, m_z)`
  (`domain/model/acciones.py`).
- Las propiedades geométricas biaxiales (`area`, `y_cdg`, `z_cdg`, `i_y`, `i_z`, `i_yz`) se
  calculan en `domain/mechanics/propiedades_seccion.py`.
- La convención de unidades asociada es mm / N / MPa / N·mm
  (ver [ADR 0004](../../decisions/0004-unidades-convencion-n-mm-mpa.md) y `domain/unidades.py`).

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

### 4.1. Propiedades características del material

El acero pasivo se describe por sus propiedades características: límite elástico `fyk`, carga
unitaria de rotura `ftk`, módulo de elasticidad `Es` y alargamiento total característico bajo carga
máxima `εuk`. El Código Estructural fija `Es = 200 GPa` y clasifica los aceros soldables en la
**Tabla 34.2.a del artículo 34** (según UNE 36065 y UNE 36068):

| Tipo de acero | `fyk` (N/mm²) | `ftk` (N/mm²) | `εmáx` barra (%) |
|---|---|---|---|
| B 400 S | ≥ 400 | ≥ 440 | ≥ 5,0 |
| B 500 S | ≥ 500 | ≥ 550 | ≥ 5,0 |
| B 400 SD | ≥ 400 | ≥ 480 | ≥ 7,5 |
| B 500 SD | ≥ 500 | ≥ 575 | ≥ 7,5 |

Se adoptan los mínimos garantizados de la tabla como valores característicos. El alargamiento
`εuk` que alimenta el diagrama de cálculo es el **alargamiento total bajo carga máxima** (`εmáx`,
`A_gt`), no el alargamiento de rotura `εu,5`: este último se mide sobre una base de cinco diámetros
y no interviene en la ley constitutiva. El alcance actual considera únicamente acero suministrado
en barra; el suministro en rollo no se modela. Las relaciones `fs/fy` y `fy,real/fy,nominal` son
criterios de recepción del producto y no datos de entrada del cálculo.

### 4.2. Diagramas de cálculo

La familia eurocódigo (EN 1992-1-1, 3.2.7, adoptada por el Código Estructural) permite dos diagramas
tensión-deformación de cálculo, ambos simétricos en tracción y compresión:

1. **Rama horizontal** (3.2.7(2), figura 3.7b): comportamiento elastoplástico perfecto, lineal
   hasta `fyd = fyk/γs` y constante hasta la deformación última `εud = 0,9·εuk`.
2. **Rama inclinada con endurecimiento** (3.2.7(1), figura 3.7a): lineal hasta `fyd` en `εyd`,
   y desde ahí crecimiento lineal hasta `ftd = ftk/γs` en `εud`.

En ambos casos, para deformaciones superiores a `εud` la ley devuelve tensión nula: el material se
considera agotado y la comprobación normativa debe detectar que se ha superado el límite último.

### 4.3. Estructura `norms/eurocode` frente a `norms/ce` y biblioteca de usuario

El Código Estructural no se implementa como un conjunto de algoritmos independiente: es la familia
eurocódigo aplicada con los parámetros nacionales españoles ([ADR 0006](../../decisions/0006-familia-eurocodigo-parametros-nacionales.md)).
Por eso las leyes de EN 1992-1-1 viven en `norms/eurocode/` y se registran bajo `NormId.CE` con los
coeficientes y etiquetas del CE desde `norms/ce/`. Los datos específicamente españoles —aceros de
la Tabla 34.2.a, clases de hormigón, cordones de pretensado y juegos de coeficientes— residen en
`norms/ce/materiales/` y `norms/ce/coeficientes.py` como **tablas abiertas**: añadir una entrada es
añadir una línea de datos, sin tocar algoritmos.

Sobre esas tablas se construye una **biblioteca de usuario** ([ADR 0010](../../decisions/0010-catalogo-generico-datos.md)):
los presets normativos se inyectan en el catálogo en la composición y son de solo lectura; el
usuario puede añadir sus propios materiales y coeficientes, que se persistirán en la base de datos.
El contrato vive en `application/ports/` y no conoce las normas.

### Vínculo con la implementación

- `AceroArmadura(fyk, ftk, es, eps_uk)` en `domain/model/materiales.py` guarda las propiedades
  características; no contiene valores de cálculo ni coeficientes de seguridad.
- Las factorías `ley_acero_pasivo_bilineal` y `ley_acero_pasivo_endurecida`
  (`norms/eurocode/laws.py`) resuelven `fyd`, `ftd` y `εud` y devuelven leyes que cumplen el
  protocolo `LeyTensionDeformacion` (`domain/mechanics/laws.py`).
- La rama horizontal reutiliza la ley genérica `LeyElastoplastica`
  (`domain/mechanics/generic_laws.py`), pues el algoritmo es idéntico; la rama inclinada se
  implementa como `LeyBilinealEndurecida`.
- `norms/ce/materiales/aceros_pasivos.py` construye los cuatro tipos de la Tabla 34.2.a con
  `acero_pasivo(nombre)`, para suministro en barra; `hormigones.py` y `aceros_pretensados.py` hacen
  lo propio con las clases HA y los cordones.
- `norms/ce/coeficientes.py` aporta los juegos de `γc` y `γs` (persistente o transitoria y
  accidental), cuya forma define `CoeficientesParciales` en `domain/value_objects/`.
- `application/almacen_catalogo.py` implementa el contrato genérico `Catalogo[T]` y unifica
  presets y entradas de usuario, protegiendo los normativos con `EntradaProtegida`. La identidad
  de un preset es `(NormId, nombre)`, de modo que varias normas pueden compartir designaciones.
- En el milestone 001, la armadura a tracción se supone plastificada (`σs = fyd`), coherente con el
  ejemplo de referencia.
