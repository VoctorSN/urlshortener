# URL Shortener API

API completa de acortador de URLs construida con FastAPI, SQLAlchemy (async) y PostgreSQL (asyncpg).

## Indice

- [Funcionalidades](#funcionalidades)
- [Stack Tecnologico](#stack-tecnologico)
- [Inicio Rapido](#inicio-rapido)
- [Documentacion de la API](#documentacion-de-la-api)
- [Tests](#tests)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Variables de Entorno](#variables-de-entorno)

## Funcionalidades

- **Acortar URLs** con codigos cortos auto-generados o aliases personalizados
- **Redireccion** via codigos cortos (HTTP 307)
- **Analytics de clicks**: navegador, sistema operativo, referrer, IP, conteo por fecha
- **Expiracion de URLs**: configura una fecha limite para tus enlaces
- **Generacion de QR codes**: obtiene un PNG con el QR de tu URL corta
- **Rate limiting**: proteccion contra abuso por IP
- **Autenticacion por token**: API Token estatico o JWT (Bearer)
- **Documentacion interactiva**: Swagger UI y ReDoc auto-generados

[↑ Volver al indice](#indice)

## Stack Tecnologico

| Componente       | Tecnologia             |
| ---------------- | ---------------------- |
| Framework        | FastAPI                |
| ORM              | SQLAlchemy 2.0 (async) |
| Base de datos    | PostgreSQL (asyncpg)   |
| Migraciones      | Alembic                |
| Tests            | pytest + httpx         |
| Containerizacion | Docker                 |

Para tests se usa SQLite en memoria (`sqlite+aiosqlite:///:memory:`).

[↑ Volver al indice](#indice)

## Inicio Rapido

### Requisitos

- Python 3.11+
- pip

### Instalacion

```bash
# Clonar el repositorio
git clone <repo-url>
cd urlshortener

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -e ".[dev]"

# Configurar variables de entorno
cp .env.example .env
# copy .env.example .env  # Windows PowerShell

# Editar .env y definir al menos un metodo de auth
# API_TOKENS=["dev-token-change-me"]
# o JWT_SECRET=tu-secreto-jwt-largo-y-aleatorio

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

### Con Docker

```bash
docker-compose up --build
```

La API estara disponible en `http://localhost:8000`.

[↑ Volver al indice](#indice)

## Documentacion de la API

Una vez corriendo el servidor:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Autenticacion

Por defecto, las rutas bajo `/api/urls/*` estan protegidas y requieren header `Authorization: Bearer <token>`.

Puedes autenticar con:

- `API_TOKENS` (token estatico)
- `JWT_SECRET` + `JWT_ALGORITHM` (JWT firmado)

Rutas publicas por defecto:

- `GET /health`
- `GET /favicon.ico`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`
- `GET /{short_code}`

### Endpoints Principales

| Metodo   | Ruta                         | Auth        | Descripcion                 |
| -------- | ---------------------------- | ----------- | --------------------------- |
| `POST`   | `/api/urls`                  | Requerida   | Crear URL corta             |
| `GET`    | `/api/urls`                  | Requerida   | Listar todas las URLs       |
| `GET`    | `/api/urls/{code}`           | Requerida   | Obtener metadata            |
| `PATCH`  | `/api/urls/{code}`           | Requerida   | Actualizar URL              |
| `DELETE` | `/api/urls/{code}`           | Requerida   | Desactivar URL              |
| `GET`    | `/{code}`                    | Publica     | Redireccion al URL original |
| `GET`    | `/api/urls/{code}/analytics` | Requerida   | Resumen de analytics        |
| `GET`    | `/api/urls/{code}/clicks`    | Requerida   | Eventos de click            |
| `GET`    | `/api/urls/{code}/qr`        | Requerida   | QR code en PNG              |
| `GET`    | `/health`                    | Publica     | Health check                |

### Ejemplo de Uso

```bash
TOKEN="dev-token-change-me"

# Crear una URL corta
curl -X POST http://localhost:8000/api/urls \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.ejemplo.com/pagina-muy-larga"}'

# Crear con alias personalizado
curl -X POST http://localhost:8000/api/urls \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.ejemplo.com", "custom_alias": "mi-link"}'

# Ver analytics
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/urls/mi-link/analytics

# Descargar QR code
curl -H "Authorization: Bearer $TOKEN" -o qr.png http://localhost:8000/api/urls/mi-link/qr

# Ruta publica (sin token)
curl -I http://localhost:8000/mi-link
```

[↑ Volver al indice](#indice)

## Tests

### Tests unitarios / de integración

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Test especifico
pytest tests/api/test_urls.py -v
```

### Tests de TestSprite (tests de caja negra contra el servidor)

> **Requisito:** el servidor debe estar corriendo en `http://localhost:8000` antes de ejecutar estos tests (via `uvicorn` o `docker compose up`).

```bash
# Ejecutar los tests de TestSprite
pytest testsprite_tests/ -v --override-ini="python_files=TC*.py test_*.py"
```

[↑ Volver al indice](#indice)

## Estructura del Proyecto

```
urlshortener/
├── app/
│   ├── main.py              # Factory de la app
│   ├── config.py             # Configuracion
│   ├── database.py           # Motor async SQLAlchemy
│   ├── models/               # Modelos ORM
│   ├── schemas/              # Schemas Pydantic
│   ├── routers/              # Endpoints API
│   └── services/             # Logica de negocio
├── alembic/                  # Migraciones de BD
├── tests/                    # Suite de tests
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

[↑ Volver al indice](#indice)

## Variables de Entorno

| Variable                        | Default                                                                                           | Descripcion                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`                  | `postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener`                             | URL de conexion a PostgreSQL                                       |
| `BASE_URL`                      | `http://localhost:8000`                                                                           | URL base publica usada para construir `short_url`                 |
| `SHORT_CODE_LENGTH`             | `7`                                                                                               | Longitud de codigos generados                                      |
| `DEFAULT_RATE_LIMIT`            | `60/minute`                                                                                       | Limite por defecto (configurable para uso futuro)                 |
| `URL_MAX_AGE_DAYS`              | `None`                                                                                            | Expiracion por defecto en dias (`None` desactiva expiracion auto) |
| `CORS_ORIGINS`                  | `["*"]`                                                                                           | Lista JSON de origenes CORS permitidos                             |
| `AUTH_ENABLED`                  | `true`                                                                                            | Activa/desactiva autenticacion global                              |
| `API_TOKENS`                    | `[]`                                                                                              | Lista JSON de tokens API aceptados                                 |
| `JWT_SECRET`                    | `None`                                                                                            | Secreto para validar JWT (HS256 por defecto)                       |
| `JWT_ALGORITHM`                 | `HS256`                                                                                           | Algoritmo JWT permitido                                            |
| `JWT_AUDIENCE`                  | `None`                                                                                            | Audience esperado en JWT (opcional)                               |
| `AUTH_PROTECTED_ROUTE_PATTERNS` | `["/api/urls/*"]`                                                                                 | Patrones de rutas protegidas                                       |
| `AUTH_EXEMPT_ROUTE_PATTERNS`    | `["GET /health","GET /favicon.ico","GET /docs","GET /redoc","GET /openapi.json","GET /{short_code}"]` | Patrones de rutas exentas de auth                                  |

Notas:

- `API_TOKENS`, `CORS_ORIGINS` y los patrones de rutas deben estar en formato lista JSON.
- Para desarrollo, define al menos `API_TOKENS` o `JWT_SECRET` para poder acceder a `/api/urls/*`.

[↑ Volver al indice](#indice)
