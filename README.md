# placas_alveolares

Aplicación de escritorio (PySide6) con arquitectura limpia (Clean Architecture).

## Stack

- **UI:** PySide6 (LGPL) — vistas en Python puro; opcionalmente `.ui` + `pyside6-uic`.
- **Persistencia:** SQLAlchemy 2.0 + Alembic. SQLite en desarrollo (configurable a PostgreSQL vía `.env`).
- **Configuración:** pydantic-settings (runtime) + `resources/` (datos estáticos).
- **Tipado:** Pyright en modo `strict`.
- **Tests:** pytest.

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
python -m placas_alveolares
```

## Documentación

- Arquitectura y decisiones: [`docs/architecture.md`](docs/architecture.md)
