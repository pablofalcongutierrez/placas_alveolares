# Arquitectura

## Capas y regla de dependencias

```
presentation ─┐
              ▼
infrastructure ──► application ──► domain
```

- `domain`: entidades, value objects, servicios y excepciones de negocio. **No depende de nada.**
- `application`: casos de uso, DTOs y **puertos** (interfaces). Depende solo de `domain`.
- `infrastructure`: adaptadores que implementan los puertos (SQLAlchemy, export, servicios externos), configuración y arranque. Depende de `application`/`domain`.
- `presentation`: UI PySide y controladores (MVP). Depende de `application`.

Regla: **las dependencias apuntan siempre hacia dentro** (`domain` no conoce a nadie).

## Estructura

```
src/placas_alveolares/
  main.py                  # entrypoint: composición + QApplication
  __main__.py              # `python -m placas_alveolares`
  domain/{entities,value_objects,services}, exceptions.py
  application/{use_cases,dtos,ports}
  infrastructure/{config,persistence,export,external_services}
  presentation/{views,controllers,widgets}
migrations/                # Alembic
resources/                 # datos estáticos
tests/{unit,integration,acceptance}
```

## Configuración

- **Runtime:** `infrastructure/config/settings.py` (pydantic-settings, prefijo `PA_`, lee `.env`).
  - `PA_DATABASE_URL` (por defecto `sqlite:///./placas.db`).
  - Cambiar a PostgreSQL = cambiar solo esa variable.
- **Estático:** carpeta `resources/`, cargada con `importlib.resources`.

## UI (PySide)

- Vistas finas + controladores (presenters) en `presentation/`.
- Flujo recomendado: Python puro; si se requiere edición visual, `.ui` en `presentation/views/ui/` y generados en `presentation/views/generated/`.

## Tipado

- Pyright en modo `strict` (`[tool.pyright]` en `pyproject.toml`).
- Excluye `migrations`, `__pycache__`.

## Roadmap

- [ ] Walking skeleton (flujo mínimo end-to-end).
- [ ] Migraciones Alembic iniciales.
- [ ] Tests unitarios (dominio/aplicación) e integración (persistencia).
