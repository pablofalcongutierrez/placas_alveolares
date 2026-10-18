# Pruebas

Documento de referencia de la estrategia de pruebas del proyecto: qué se prueba
en cada nivel, cómo está organizada la suite, cómo se ejecuta y qué convenciones
seguir al añadir tests. La sección «Pruebas» de [`architecture.md`](architecture.md)
se mantiene como resumen y enlaza aquí.

## 1. Propósito y filosofía

La suite persigue dos objetivos: **proteger la corrección del núcleo de cálculo**
y **dejar constancia verificable** de que los resultados coinciden con la teoría
y con los ejemplos de referencia de la bibliografía (material reutilizable en la
memoria del TFM).

La estrategia sigue una **pirámide**:

| Nivel | Carpeta | Qué se prueba | Por qué aquí |
|---|---|---|---|
| Unitario (dominio) | `tests/unit/domain/` | VOs, validaciones y motores contra **soluciones analíticas** e invariantes | Rápido, sin modelo completo ni norma |
| Unitario (normas) | `tests/unit/norms/<norma>/` | `run(data, params)` con **escalares**, sin modelo | Un check es función pura: se aísla la regla normativa |
| Unitario (aplicación) | `tests/unit/application/` | Preparadores y catálogo | Verifica el pegamento sin depender de normas |
| Integración | `tests/integration/` | Casos de uso end-to-end y comparación entre normas | Comprueba la composición real |
| Aceptación | `tests/acceptance/` | Flujos completos (controladores/UI) | Único lugar donde se valida la UI |

Principios rectores:

- Un test verifica **un comportamiento** y usa las **unidades del núcleo** (mm, N, MPa, N·mm).
- Los comparadores de flotantes usan `pytest.approx`; nunca igualdad exacta.
- Los tests son **independientes y sin estado compartido**: no hay fixtures globales ni orden implícito.
- Se privilegian **invariantes** (equilibrio de tensiones, coherencia de áreas) sobre valores copiados.

**Qué NO se cubre con tests unitarios** (y dónde sí): la UI se valida en
`tests/acceptance/`; no se prueba el detalle de librerías externas (PySide6,
SQLAlchemy, mapbox-earcut) ni máquinas de estado complejas; el tipado estático se
delega en Pyright, no en tests.

## 2. Organización actual

```
tests/
  __init__.py
  unit/
    __init__.py
    domain/
      __init__.py
      test_geometria.py             # 7 tests
      test_seccion.py               # 6 tests
      test_fases.py                 # 3 tests
      test_propiedades_seccion.py   # 9 tests
      test_mallado.py               # 4 tests
      test_integracion.py           # 8 tests
  integration/                      # solo __init__.py (pendiente)
  acceptance/                       # solo __init__.py (pendiente)
```

Total actual: **37 tests**, todos en `tests/unit/domain/`.

| Fichero | Cobertura |
|---|---|
| `test_geometria.py` | Validación de `Contorno` (≥ 3 vértices); `rectangulo()` (incluido desplazamiento en `y`); `circulo()` (polígono inscrito, valor por defecto y validaciones) |
| `test_seccion.py` | Invariantes de `Seccion` y `ModeloEstructural`; esfuerzos internos biaxiales (N, M_y, M_z) |
| `test_fases.py` | `componentes_activos()` por fase y `componentes_adheridos()` (excluye enfundados) |
| `test_propiedades_seccion.py` | Área, cdg, inercias e producto de inercia (rectángulo, hueco, L, círculo, comparación de reglas) |
| `test_mallado.py` | Triangulación con y sin huecos, círculo poligonizado, hueco fuera del contorno |
| `test_integracion.py` | Suma de pesos, integrales exactas de grado ≤ 2 (y, z, y·z) y comparación de reglas |

## 3. Configuración

Toda la configuración vive en `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- `testpaths`: ejecutar `pytest` sin argumentos explora solo `tests/`.
- `pythonpath`: añade `src/` al `sys.path`, de modo que la suite funciona **sin instalar** el paquete.
- **No hay** `conftest.py`, ni marcadores (`markers`), ni `addopts`, ni `pytest-cov`, ni configuración de CI.
- **Requisito de entorno:** Python 3.12. Se recomienda un `.venv` con las dependencias instaladas
  (`pip install -e ".[dev]"`), que incluye `pytest>=8.0` y `pyright>=1.1.380`.

## 4. Comandos de ejecución (Windows PowerShell)

Con el entorno virtual activado:

```powershell
.venv\Scripts\activate
pytest                         # suite completa
```

Sin activar el venv (invocando su intérprete directamente):

```powershell
.venv\Scripts\python.exe -m pytest
```

Selecciones habituales:

```powershell
pytest tests\unit\domain\test_geometria.py           # un fichero
pytest tests\unit\domain\test_geometria.py::test_rectangulo_dimensiones   # un test
pytest -v                                             # nombre de cada test
pytest -vv -s                                         # traza detallada y salida de stdout
pytest -k propiedades                                 # por palabra clave
pytest --collect-only                                 # listar sin ejecutar
```

**Puerta de calidad** antes de cerrar una tarea (ver [`../AGENTS.md`](../AGENTS.md)):

```powershell
pyright        # tipado estático (modo strict)
pytest         # suite verde
```

## 5. Cómo escribir un test nuevo

**Ubicación según la capa:**

| Qué testeas | Dónde |
|---|---|
| VOs, validaciones, motores de `domain` | `tests/unit/domain/` |
| Un check normativo llamando a `run` con escalares | `tests/unit/norms/<norma>/` |
| Preparadores y catálogo | `tests/unit/application/` |
| Casos de uso end-to-end / comparación de normas | `tests/integration/` |
| Flujos de UI/controladores | `tests/acceptance/` |

**Convenciones:**

- Fichero `test_*.py`, función `test_*`, nombres y docstring **en español** (una
  línea que describa el comportamiento, no el nombre de la función).
- Importaciones absolutas desde `placas_alveolares(...)`; `from __future__ import annotations`
  como primera línea tras el docstring.
- Flotantes siempre con `pytest.approx`; excepciones esperadas con `pytest.raises`.
- **Sin lógica condicional** de control dentro de los tests: un caso, un `assert`
  representativo. **Sin fixtures compartidas**: los datos se construyen con helpers
  locales `_algo()`.

Ejemplo de test unitario del dominio:

```python
from placas_alveolares.domain.mechanics.propiedades_seccion import propiedades_geometricas
from placas_alveolares.domain.model.geometria import rectangulo


def test_rectangulo_300x500() -> None:
    """Rectángulo 300×500 con base en z=0."""
    propiedades = propiedades_geometricas(rectangulo(300.0, 500.0, z_base=0.0))

    assert propiedades.area == pytest.approx(150_000.0)
    assert propiedades.z_cdg == pytest.approx(250.0)
    assert propiedades.i_y == pytest.approx(3.125e9)
```

Usa `pytest.raises` cuando el contrato sea **rechazar una entrada inválida**:

```python
def test_seccion_exige_al_menos_un_componente() -> None:
    """Una sección sin componentes no es válida."""
    with pytest.raises(ValueError):
        Seccion(componentes=())
```

## 6. Estado actual y evolución prevista

**Pendiente hoy:**

- `tests/integration/` y `tests/acceptance/` contienen solo `__init__.py`.
- No hay tests de normas ni de aplicación (llegan con el milestone 001).

**Propuestas futuras** (no implantadas):

- `pytest-cov` para medir cobertura y fijar un umbral mínimo.
- Marcadores (`@pytest.mark.integration`, `@pytest.mark.slow`) para separar suites por coste.
- CI (GitHub Actions u equivalente) que ejecute `pyright` y `pytest` en cada push.

## 7. Referencias

- [`../AGENTS.md`](../AGENTS.md) — comandos, convenciones de código y flujo de trabajo (SDD).
- [`architecture.md`](architecture.md) — capas, contratos de comprobación y sección «Pruebas».
- [`decisions/`](decisions/) — ADRs; en particular `0001` (frontera mecánica/normativa),
  `0002` (checks como funciones puras tipadas) y `0008` (mallado y cuadratura).
- [`specs/`](specs/) — por milestone; `tasks.md` lista los tests a crear y
  `bases_calculo.md` aporta los ejemplos de referencia con los que validar.
