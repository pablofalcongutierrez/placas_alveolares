# AGENTS.md

Guía para agentes que trabajan en este repositorio. Léela antes de escribir código.

## Qué es el proyecto

Herramienta de escritorio de **cálculo seccional estructural** (hormigón, acero y pretensado), desarrollada como Trabajo Fin de Máster. El foco inicial son las **placas alveolares pretensadas**, pero la arquitectura está pensada para incorporar progresivamente más tipos de cálculo y más normativas (Código Estructural, Eurocódigo 2, EN 1168, EHE-08, ACI 318…).

## Stack y comandos

- **Lenguaje:** Python 3.12.
- **UI:** PySide6. **Persistencia:** SQLAlchemy 2.0 + Alembic (SQLite en desarrollo).
- **Configuración:** pydantic-settings. **Tipado:** Pyright en modo `strict`. **Tests:** pytest.

```powershell
.venv\Scripts\activate
pip install -e ".[dev]"          # instalar dependencias
pyright                          # verificación de tipos (modo strict)
pytest                           # ejecutar tests
alembic upgrade head             # aplicar migraciones
python -m placas_alveolares      # ejecutar la aplicación
```

Antes de dar una tarea por terminada: **`pyright` limpio y `pytest` verde.**

## Estructura

La arquitectura completa está en [`docs/architecture.md`](docs/architecture.md). Resumen de capas:

```
presentation / infrastructure ──► application ──► domain ◄── norms ◄── main.py (composition root)
```

- `domain/` — modelo estructural, mecánica, estados y contratos de comprobación. **No depende de nada.**
- `norms/` — plugins normativos (implementaciones de normas). Dependen solo de `domain`.
- `application/` — catálogo, casos de uso, DTOs y puertos. Depende solo de `domain`. **No importa `norms`.**
- `infrastructure/`, `presentation/` — adaptadores y UI.
- `main.py` — **único** punto que importa las normas y las registra.

## Reglas arquitectónicas inviolables

1. **Las dependencias apuntan hacia dentro.** `domain` no importa `application`, `norms`, `infrastructure` ni `presentation`.
2. **El núcleo no conoce normativas concretas.** `domain` y `application` nunca importan `norms`. Solo `main.py` (composition root) las conoce.
3. **Un check es una función pura.** Recibe un dataclass de entrada específico y uno de parámetros; nunca el modelo del proyecto ni acceso global. No "rebusca" datos.
4. **Tipado estricto, sin excepciones.** Prohibido `**kwargs` y diccionarios genéricos como mecanismo de comunicación. Cada input, parámetros y resultado es un dataclass `frozen` con `slots`.
5. **Unidades fijas:** mm, N, MPa, N·mm en todo el núcleo. Conversiones solo en las fronteras.
6. **Toda comprobación emite traza** (`CalcStep`) con símbolo, valor, unidad y cláusula.
7. **Selección por catálogo, nunca por condicional central.** Registrar/consultar `(NormId, CheckKind)`; no cadenas `if norma == ...`.
8. **Reutilización solo si el algoritmo es idéntico** (p. ej. CE/EC2 con parámetros nacionales). Ante la duda, implementaciones separadas.

El razonamiento y las alternativas descartadas de estas reglas están en [`docs/decisions/`](docs/decisions/).

## Convenciones de código

- Dataclasses `@dataclass(frozen=True, slots=True)` para datos; `typing.Protocol` para contratos.
- `StrEnum` para vocabularios cerrados (`CheckKind`, `NormId`, `DetailLevel`).
- **Código nuevo íntegramente en español**: identificadores (clases, funciones, variables, campos), docstrings y comentarios. El código existente en inglés (`get_settings`, `Settings`, `MainWindow`, `Base`…) no se modifica de momento.
- Docstrings estructurados en **formato Google** (`Args:`, `Returns:`, `Raises:`, `Attributes:`), en español.
- Comentarios solo cuando aportan; evitar comentarios que repitan el código.
- Sin `print` para depuración; usar el logger configurado.

## Recetas

### Añadir una norma
1. Crear `norms/<nombre>/` con `params.py`, `laws.py` (si aporta leyes), `inputs.py`, los checks y `module.py`.
2. En `module.py`, implementar `register(catalog: CheckCatalog) -> None` registrando los descriptores.
3. En el composition root (`main.py`), importar el paquete y llamar a su `register(catalog)`.
4. Añadir los tests de ejemplos de referencia en `tests/unit/norms/<nombre>/`.

### Añadir una comprobación
1. Si es un tipo nuevo, añadirlo a `CheckKind` (es vocabulario, no un condicional).
2. Definir el dataclass de entrada específico, el de parámetros (si aplica) y el resultado (hereda de `CheckResult`).
3. Implementar `run(data, params) -> resultado` construyendo la traza con `TraceBuilder`.
4. Crear el preparador modelo → entrada y la función de aplicabilidad.
5. Registrar el descriptor en el `module.py` de la norma correspondiente.

### Añadir un parámetro nacional
Añadirlo al dataclass de parámetros de la norma con valor por defecto; el preparador lo propaga. Es un cambio aditivo: no rompe normas ni tests existentes.

## Cómo trabajar con las especificaciones (SDD)

Las unidades de trabajo son las especificaciones en [`docs/specs/`](docs/specs/). Cada milestone tiene una carpeta `NNN-nombre/` con:

- `spec.md` — qué y por qué: alcance, requisitos y **criterios de aceptación**.
- `bases_calculo.md` — fundamentos teóricos del milestone, **aislados de la implementación** (reutilizables en la memoria del TFM). Termina cada apartado con un breve "Vínculo con la implementación".
- `plan.md` — cómo: diseño técnico, archivos y tipos a crear.
- `tasks.md` — checklist ejecutable y marcable.

**Flujo de una sesión:** lee este `AGENTS.md` → `docs/architecture.md` → la `spec` del milestone activo (y su `bases_calculo.md` cuando exista) → implementa las tareas de `tasks.md` marcándolas al completarlas → ejecuta `pyright` y `pytest`.

Las specs de milestones futuros se escriben **justo antes** de abordarlos, no por adelantado.

## Documentación

- [`docs/architecture.md`](docs/architecture.md) — arquitectura y decisiones de alto nivel.
- [`docs/testing.md`](docs/testing.md) — estrategia de pruebas, organización, comandos y convenciones.
- [`docs/decisions/`](docs/decisions/) — ADRs (contexto, decisión, alternativas, consecuencias).
- [`docs/specs/`](docs/specs/) — especificaciones por milestone.

**Mantén este archivo actualizado** cuando cambien los comandos, la estructura o las reglas.
