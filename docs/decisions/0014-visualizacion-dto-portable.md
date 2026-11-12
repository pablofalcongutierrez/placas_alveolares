# 0014 — Visualización mediante un DTO portable, no mediante widgets compartidos

## Contexto

La aplicación necesita representar la evolución de deformaciones y tensiones de
una sección: planta girada, línea neutra horizontal y diagramas alineados. La
primera interfaz será PySide, pero el mismo resultado debe poder mostrarse en
web, Electron, informes o exportaciones sin reimplementar la mecánica ni
duplicar el modelo estructural.

Existen varias alternativas:

1. Hacer que el dominio devuelva objetos gráficos o listas de dibujo.
2. Compartir un widget o un renderizador abstracto entre todas las interfaces.
3. Generar imágenes o SVG en el núcleo y consumirlas como recurso.
4. Proyectar el cálculo a un contrato de datos neutral y dejar el dibujo a cada
   adaptador.

## Decisión

Se adopta la alternativa 4.

- El **dominio** calcula la alineación mecánica y evalúa deformaciones y
  tensiones. No conoce colores, píxeles ni paneles.
- La **aplicación** construye un DTO inmutable con magnitudes físicas:
  geometría efectiva en coordenadas alineadas, perfiles, rangos y metadatos de
  fase.
- Cada **presentación** implementa su propio dibujo e interacción sobre ese
  contrato: PySide con `QPainter`, web con Canvas/SVG, Electron con su frontend
  o un cuaderno con Matplotlib.

El contrato usa unidades del núcleo (mm, tanto por uno y MPa) y no contiene
tipos de Qt, NumPy ni entidades del modelo. La serialización JSON y la
exposición HTTP se consideran adaptadores de infraestructura posteriores.

## Consecuencias

- La visualización no puede desincronizarse de la fórmula constitutiva: ambas
  usan `evaluar_tension` y el plano constitutivo del estado.
- Los tests del contrato no necesitan una UI.
- Cambiar de PySide a web no exige tocar `domain` ni `application`.
- Cada interfaz debe volver a implementar su dibujo. Se acepta conscientemente:
  un abstracción común de canvas acabaría filtrando conceptos gráficos al
  núcleo y limitaría las capacidades propias de cada plataforma.
- La evolución representa estados discretos al final de cada fase. Una
  evolución temporal continua requerirá ampliar el análisis temporal del
  dominio.
