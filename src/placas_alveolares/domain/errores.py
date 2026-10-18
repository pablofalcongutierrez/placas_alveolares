"""Errores tipados del dominio estructural.

Todos los errores del núcleo derivan de :class:`ErrorDominio`, de modo que las
capas exteriores puedan capturar un único tipo raíz. La jerarquía distingue dos
familias:

- :class:`ErrorValidacion`: una entrada incumple una invariante del modelo
  (geometría, material, sección, fases o modelo).
- :class:`ErrorCalculo`: un motor numérico no puede completar su cálculo.

La convención se extiende al resto de capas (normas, aplicación,
infraestructura y presentación): cada una define su propia base
(``ErrorAplicacion``, ``ErrorNorma``…) heredando de :class:`ErrorDominio`. El
razonamiento está en ``docs/decisions/0009-errores-tipados-por-capas.md``.
"""

from __future__ import annotations


class ErrorDominio(Exception):
    """Error raíz del núcleo estructural."""


class ErrorValidacion(ErrorDominio):
    """Entrada que incumple una invariante del modelo estructural."""


class ErrorCalculo(ErrorDominio):
    """Fallo numérico o de un motor de cálculo."""


class GeometriaInvalida(ErrorValidacion):
    """Geometría de sección inválida (contorno, dimensiones o huecos)."""


class MaterialInvalido(ErrorValidacion):
    """Propiedad física de un material no válida."""


class SeccionInvalida(ErrorValidacion):
    """Sección transversal o componente inválido."""


class FaseInvalida(ErrorValidacion):
    """Fase constructiva inválida."""


class ModeloInvalido(ErrorValidacion):
    """Modelo estructural incoherente."""


class ErrorMallado(ErrorCalculo):
    """Fallo del motor de mallado."""
