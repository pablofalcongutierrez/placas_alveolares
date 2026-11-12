# Bases de cálculo — Visualización alineada con la línea neutra

## 1. Plano de deformaciones

La hipótesis de Bernoulli–Navier con flexión biaxial establece:

\[
\varepsilon(y,z)=\varepsilon_0+\kappa_y z-\kappa_z y
\]

La deformación es positiva a tracción. El plano común es el estado cinemático
de la sección; la deformación que ve la ley de cada componente es:

\[
\Phi_i=\Phi_\text{común}-\Phi_{\text{referencia},i}
+\Phi_{\text{impuesta},i}
\]

Por ello, la fibra de tensión nula de un componente puede no coincidir con la
línea neutra común.

## 2. Curvatura y dirección de la línea neutra

El gradiente de deformación del plano común es:

\[
\nabla\varepsilon=(-\kappa_z,\kappa_y)
\]

La curvatura resultante y su dirección unitaria son:

\[
\kappa=\sqrt{\kappa_y^2+\kappa_z^2}
\]

\[
\mathbf{n}=\frac{(-\kappa_z,\kappa_y)}{\kappa}
\]

La línea neutra es el lugar geométrico \(\varepsilon=0\). Su dirección tangente
es perpendicular a \(\mathbf{n}\):

\[
\mathbf{t}=\frac{(\kappa_y,\kappa_z)}{\kappa}
\]

## 3. Sistema alineado

Se definen las coordenadas:

\[
u=\mathbf{t}\cdot(y,z)=\frac{\kappa_y y+\kappa_z z}{\kappa}
\]

\[
q=\mathbf{n}\cdot(y,z)=\frac{-\kappa_z y+\kappa_y z}{\kappa}
\]

La línea neutra se encuentra en:

\[
q_{LN}=-\frac{\varepsilon_0}{\kappa}
\]

Trasladando el origen vertical a la línea neutra:

\[
v=q-q_{LN}=q+\frac{\varepsilon_0}{\kappa}
\]

se obtiene:

\[
\boxed{\varepsilon=\kappa v}
\]

Así, la línea neutra queda horizontal en \(v=0\). La transformación inversa es:

\[
y=\cos\theta\,u-\sin\theta\,(v+q_{LN})
\]

\[
z=\sin\theta\,u+\cos\theta\,(v+q_{LN})
\]

con \(\cos\theta=\kappa_y/\kappa\) y \(\sin\theta=\kappa_z/\kappa\).

**Vínculo con la implementación:**
`domain/mechanics/alineacion_deformaciones.py` construye el sistema y aplica
ambas transformaciones.

## 4. Caso degenerado

Si \(\kappa\approx 0\) no existe una dirección única de línea neutra:

- con \(\varepsilon_0\neq 0\), la deformación es uniforme y no nula;
- con \(\varepsilon_0=0\), la deformación es idéntica a cero.

En ambos casos se conserva la orientación original y se marca
`linea_neutra_definida = False`. El umbral empleado es
\(10^{-12}\ \mathrm{mm^{-1}}\).

**Vínculo con la implementación:** el indicador se propaga al DTO y el
renderizador decide si dibuja la línea.

## 5. Perfiles por componente

La sección es biaxial. Para un componente cualquiera, la tensión es una función
de dos coordenadas:

\[
\sigma_i=\sigma_i(u,v)
\]

Una única curva de tensión por material no representa toda la variación
transversal. En esta primera versión se extrae un perfil vertical por componente
en:

\[
u=u_{c,i}
\]

donde \(u_{c,i}\) es la coordenada tangente del centroide de su malla efectiva.
Sobre esa vertical se evalúan deformación constitutiva y tensión. La
pertenencia al componente se comprueba contra su malla triangular, de modo que
los huecos dividen el perfil en tramos y no se dibuja material inexistente.

Los perfiles de todos los componentes comparten la misma cota \(v\). Los
componentes enfundados se representan con su tensión propia, aunque no
contribuyan a las resultantes de equilibrio.

**Vínculo con la implementación:**
`application/use_cases/visualizar_tensiones.py` construye los perfiles y
`domain/mechanics/campo_tensiones.py` evalúa la tensión.

## 6. Lectura conjunta

Para comparar fases se emplea:

- una escala vertical global;
- una escala de deformaciones global;
- una escala de tensiones global, o escalas separadas por material cuando la
  diferencia entre hormigón y pretensado oculta la forma de una de ellas.

La escala global de tensiones no altera los datos: es una decisión del
adaptador de presentación.

**Vínculo con la implementación:** el DTO publica rangos por fase y globales;
el cuaderno los usa para fijar los ejes.
