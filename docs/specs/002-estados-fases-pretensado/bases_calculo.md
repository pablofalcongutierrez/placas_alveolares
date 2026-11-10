# Bases de cálculo — Milestone 002

## 1. Plano común y referencias

La hipótesis de Bernoulli–Navier establece un plano cinemático común para los
componentes adheridos:

```text
ε(y,z) = ε₀ + κ_y·z − κ_z·y
```

Cada componente puede tener una deformación impuesta propia —por ejemplo, el
pretensado— y una referencia de activación. La deformación que se evalúa en su
ley constitutiva es:

```text
ε_constitutiva = Φ_común − Φ_referencia + ε_impuesta
```

La referencia representa el plano en el que el componente quedó libre de
tensión. Al adherir un tendón, la referencia se fija al plano común vigente.

## 2. Fases y equilibrio

Cada fase contiene acciones totales, operaciones y un indicador de resolución.
Las operaciones se aplican al final del intervalo. Si la fase resuelve, el
equilibrio se calcula en `tiempo_fin`:

```text
N_int = ∫σ dA,  M_y,int = −∫σ·z dA,  M_z,int = ∫σ·y dA
```

Las fases de tesado o pérdidas pueden no resolver equilibrio y conservar el
plano común anterior.

## 3. Pretensado

La fuerza de tesado se convierte en deformación mediante:

```text
ε_p0 = P0 / (A_p · E_p)
```

La tensión inicial se convierte con `ε_p0 = σ_p0/E_p`. Las pérdidas se aplican
como una reducción de la deformación impuesta y no pueden invertir el signo
del pretensado.

## 4. Superposición geométrica

Un cordón o barra embebida ocupa un volumen que no puede contarse a la vez como
hormigón y como acero. El contorno del componente embebido se añade como hueco
del contorno de su anfitrión y el hormigón se malla descontando ese hueco. El
acero se malla por separado. La integración no aplica ninguna corrección
tensional equivalente.
