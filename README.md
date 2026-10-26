# Placas alveolares

Herramienta de escritorio de **cálculo seccional estructural**, desarrollada como Trabajo Fin de Máster. Su foco inicial son las **placas alveolares pretensadas**, pero la arquitectura está pensada para incorporar progresivamente hormigón armado, acero, pretensado y distintas normativas (Código Estructural, Eurocódigo 2, EN 1168, EHE-08, ACI 318…).

## Estado

Proyecto **en desarrollo**. La base arquitectónica y el núcleo geométrico/mecánico ya están operativos; la primera comprobación completa está en curso.

- **Implementado:** modelo estructural por componentes y fases, mallado y cuadratura, propiedades de sección, leyes constitutivas genéricas, leyes del hormigón y del acero según eurocódigo, tablas de materiales y coeficientes del Código Estructural, y catálogo genérico de datos normativos.
- **En curso:** comprobación de flexión ELU, catálogo de comprobaciones y casos de uso.
- **Pendiente:** cortante, pretensado y evolución temporal, ELS, persistencia del modelo y UI completa (la ventana actual es un placeholder).

## Características de diseño

- **Núcleo independiente de la normativa:** la mecánica (equilibrio, compatibilidad, integración de tensiones) vive en `domain`; las leyes constitutivas y los criterios de verificación se inyectan desde cada norma.
- **Plugins normativos:** cada norma se registra en un catálogo como `(NormId, CheckKind)`, sin condicionales centrales ni imports de `norms` desde `domain` o `application`.
- **Comprobaciones puras y tipadas:** cada check recibe dataclasses de entrada y parámetros, y devuelve un resultado con `ratio`, veredicto, cláusula y traza de cálculo.
- **Trazabilidad:** toda comprobación emite pasos de cálculo con símbolo, valor, unidad y referencia normativa.
- **Unidades coherentes en el núcleo:** mm, N, MPa y N·mm; las conversiones se realizan solo en las fronteras.
- **Arquitectura limpia:** dependencias hacia dentro y un único composition root que conoce las normas.

## Stack

| Área | Tecnología |
|---|---|
| Lenguaje | Python 3.12 |
| Interfaz | PySide6 |
| Persistencia | SQLAlchemy 2.0 + Alembic (SQLite en desarrollo, PostgreSQL configurable) |
| Configuración | pydantic-settings |
| Tipado | Pyright en modo `strict` |
| Pruebas | pytest |
| Cálculo numérico | NumPy + mapbox-earcut |

## Requisitos

- Python 3.12 o superior.
- Windows, Linux o macOS.
- No se necesita un servidor de base de datos para desarrollo: SQLite es el valor por defecto.

## Puesta en marcha

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
python -m placas_alveolares
```

**Linux / macOS**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m placas_alveolares
```

También puede lanzarse con el comando instalado:

```bash
placas-alveolares
```

Para trabajar con los cuadernos, instala el extra correspondiente:

```bash
pip install -e ".[dev,notebooks]"
```

> Las migraciones (`alembic upgrade head`) son opcionales mientras no existan revisiones en `migrations/versions/`.

## Configuración

La aplicación lee variables con prefijo `PA_` desde el entorno o desde `.env`:

| Variable | Por defecto | Descripción |
|---|---|---|
| `PA_DATABASE_URL` | `sqlite:///./placas.db` | URL de conexión de SQLAlchemy |
| `PA_LOG_LEVEL` | `INFO` | Nivel de registro |
| `PA_EXPORT_DIR` | `./exports` | Directorio de exportación |

## Calidad

Antes de dar una tarea por terminada, el repositorio debe quedar con tipado limpio y suite verde:

```powershell
pyright
pytest
```

- `pyright` verifica todo `src` en modo `strict`.
- `pytest` ejecuta las pruebas de dominio, normas y aplicación.

## Arquitectura

```
presentation / infrastructure ──► application ──► domain ◄── norms ◄── main.py
```

- `domain` — modelo estructural, mecánica, estados y contratos de comprobación. No depende de nada.
- `norms` — plugins normativos autocontenidos. Dependen solo de `domain`.
- `application` — catálogo, casos de uso, DTOs y puertos. Depende solo de `domain`; no importa `norms`.
- `infrastructure` / `presentation` — adaptadores, configuración y UI.
- `main.py` — composition root: único punto que importa y registra las normas.

La explicación completa, los contratos y las decisiones están en [`docs/architecture.md`](docs/architecture.md).

## Estructura

```
src/placas_alveolares/
  domain/          # modelo, mecánica, estados y contratos
  norms/           # plugins normativos (CE, EC2, EN 1168)
  application/     # catálogo, casos de uso, DTOs y puertos
  infrastructure/  # configuración, persistencia y exportación
  presentation/    # UI PySide6
  main.py          # composition root
tests/             # unit, integration y acceptance
docs/              # arquitectura, ADRs, specs y testing
migrations/        # Alembic
resources/         # datos e imágenes estáticas
notebooks/         # cuadernos de apoyo
```

## Documentación

- [`docs/architecture.md`](docs/architecture.md) — capas, contratos y conceptos del cálculo seccional.
- [`docs/testing.md`](docs/testing.md) — estrategia, organización y convenciones de las pruebas.
- [`docs/decisions/`](docs/decisions/) — ADRs con contexto, decisión y alternativas.
- [`docs/specs/`](docs/specs/) — especificaciones por milestone: qué, bases de cálculo, plan y tareas.
- [`AGENTS.md`](AGENTS.md) — comandos, convenciones de código y flujo de trabajo.

## Roadmap

1. Walking skeleton: geometría con huecos → propiedades → flexión ELU del Código Estructural de punta a punta, con traza.
2. Separación CE/EC2 dentro de la familia eurocódigo y comparación entre normas.
3. Cortante: eurocódigo (CE/EC2) y módulo EN 1168 con aplicabilidad restringida.
4. Pretensado y evolución temporal: pérdidas, transferencia y servicio.
5. ELS: limitación de tensiones y fisuración.
6. Normas adicionales (EHE-08, ACI 318) como validación de extensibilidad.
