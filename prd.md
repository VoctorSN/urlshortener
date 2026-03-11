# PRD - URL Shortener API

## Meta

| Campo      | Valor              |
| ---------- | ------------------ |
| Proyecto   | URL Shortener API  |
| Version    | 1.0.0              |
| Fecha      | 2026-03-11         |
| Tipo       | Backend API (REST) |
| Puerto     | 8000               |
| Test scope | codebase           |

## Product Overview

API REST de acortador de URLs construida con FastAPI (Python) y SQLAlchemy 2.0 async sobre SQLite (aiosqlite). Permite crear URLs cortas con codigos auto-generados o aliases personalizados, redirigir mediante codigos cortos, rastrear analytics de clicks (navegador, OS, referrer, IP), generar QR codes en PNG, configurar expiracion de URLs y aplicar rate limiting por IP. La aplicacion expone documentacion interactiva via Swagger UI (`/docs`) y ReDoc (`/redoc`). Utiliza Alembic para migraciones de base de datos y soporte para despliegue en Docker.

## Core Goals

- Permitir a los usuarios acortar URLs largas en codigos cortos unicos y compartibles.
- Proporcionar redireccion rapida via HTTP 307 para mantener tracking de analytics.
- Recopilar analytics detallados de cada click: navegador, sistema operativo, referrer, IP, fecha.
- Soportar aliases personalizados con validacion de formato y reserva de rutas del sistema.
- Permitir expiracion temporal de URLs con validacion de fechas futuras.
- Generar QR codes en formato PNG para cualquier URL corta.
- Proteger la API contra abuso mediante rate limiting por IP.
- Soft-delete de URLs (desactivacion) manteniendo acceso a la metadata.

## Key Features

- **Acortamiento de URLs**: Generacion de codigos cortos criptograficamente seguros (`secrets.token_urlsafe`) o aliases personalizados (3-30 chars, alfanumerico + guiones).
- **Redireccion**: HTTP 307 Temporary Redirect para permitir tracking continuo de analytics.
- **Click Analytics**: Registro de cada click con parsing de User-Agent (navegador, OS), IP, referrer, timestamp. Resumen agregado con total clicks, visitantes unicos, distribucion de navegadores/OS/referrers, clicks por fecha. Filtrado por rango de fechas.
- **QR Code**: Generacion de PNG con tamano configurable (1-40 box size) y correccion de errores media.
- **Expiracion**: Fecha de expiracion opcional; URLs expiradas retornan 410 Gone en redireccion pero siguen accesibles via metadata.
- **Rate Limiting**: Limites por endpoint via slowapi (30-120 req/min segun endpoint).
- **CRUD completo**: Crear, leer, listar (paginado), actualizar parcial y soft-delete de URLs.
- **Validacion**: Pydantic v2 para validacion de URLs (HttpUrl), fechas futuras, y formato de aliases. Rutas reservadas bloqueadas como aliases.

## Tech Stack

| Componente    | Tecnologia                              |
| ------------- | --------------------------------------- |
| Lenguaje      | Python 3.11+ (Docker usa 3.12)          |
| Framework     | FastAPI >=0.115.0                       |
| ORM           | SQLAlchemy 2.0 (async, aiosqlite)       |
| Base de datos | SQLite (aiosqlite >=0.20.0)             |
| Migraciones   | Alembic >=1.13.0                        |
| Rate Limiting | slowapi >=0.1.9                         |
| QR Codes      | qrcode >=7.4 + Pillow >=10.0.0          |
| UA Parsing    | user-agents >=2.2.0                     |
| Validacion    | Pydantic v2 (pydantic-settings >=2.3.0) |
| URL Valid.    | validators >=0.28.0                     |
| Tests         | pytest >=8.0 + pytest-asyncio + httpx   |
| Servidor      | Uvicorn (standard) >=0.30.0             |
| Container     | Docker (multi-stage) + docker-compose   |

## User Flow Summary

1. El usuario envia un POST a `/api/urls` con una URL original (y opcionalmente un alias personalizado y/o fecha de expiracion).
2. La API valida la URL, genera o valida el codigo corto, lo almacena en la base de datos y retorna la URL corta completa.
3. Cualquier visitante accede a `/{short_code}` y es redirigido (307) a la URL original. Se registra un evento de click con su informacion (IP, User-Agent, referrer).
4. El usuario consulta analytics via `GET /api/urls/{code}/analytics` para ver resumen agregado, o `/clicks` para eventos individuales paginados.
5. El usuario genera un QR code via `GET /api/urls/{code}/qr` que retorna un PNG descargable.
6. El usuario puede actualizar la URL (PATCH) o desactivarla (DELETE) en cualquier momento.
7. URLs expiradas o desactivadas retornan 410 Gone al intentar redireccion, pero su metadata sigue accesible.

## API Endpoints

### Health & Utility

| Metodo | Ruta           | Rate Limit | Status | Descripcion                          |
| ------ | -------------- | ---------- | ------ | ------------------------------------ |
| GET    | `/health`      | -          | 200    | Health check: `{"status":"healthy"}` |
| GET    | `/favicon.ico` | -          | 204    | Suprime 404 del navegador            |

### URL CRUD (`/api/urls`)

| Metodo | Ruta               | Rate Limit | Status | Descripcion                  |
| ------ | ------------------ | ---------- | ------ | ---------------------------- |
| POST   | `/api/urls`        | 30/min     | 201    | Crear URL corta              |
| GET    | `/api/urls`        | 60/min     | 200    | Listar URLs (paginado)       |
| GET    | `/api/urls/{code}` | 60/min     | 200    | Obtener metadata de URL      |
| PATCH  | `/api/urls/{code}` | 30/min     | 200    | Actualizar URL               |
| DELETE | `/api/urls/{code}` | 30/min     | 204    | Desactivar URL (soft-delete) |

### Redireccion

| Metodo | Ruta            | Rate Limit | Status | Descripcion                             |
| ------ | --------------- | ---------- | ------ | --------------------------------------- |
| GET    | `/{short_code}` | 120/min    | 307    | Redirige a URL original, registra click |

### Analytics (`/api/urls`)

| Metodo | Ruta                         | Rate Limit | Status | Descripcion                   |
| ------ | ---------------------------- | ---------- | ------ | ----------------------------- |
| GET    | `/api/urls/{code}/analytics` | 60/min     | 200    | Resumen agregado de analytics |
| GET    | `/api/urls/{code}/clicks`    | 60/min     | 200    | Eventos de click paginados    |

### QR Code

| Metodo | Ruta                  | Rate Limit | Status | Descripcion    |
| ------ | --------------------- | ---------- | ------ | -------------- |
| GET    | `/api/urls/{code}/qr` | 30/min     | 200    | QR code en PNG |

## Request/Response Schemas

### URLCreate (POST body)

```json
{
  "original_url": "https://example.com/long-url",
  "custom_alias": "my-link",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

- `original_url` (requerido): URL valida (Pydantic HttpUrl).
- `custom_alias` (opcional): 3-30 chars, `^[a-zA-Z0-9_-]+$`. No puede ser una ruta reservada (`api`, `health`, `docs`, `redoc`, `openapi.json`, `favicon.ico`).
- `expires_at` (opcional): Datetime UTC, debe ser en el futuro. Validado con `model_validator` en Pydantic.

### URLResponse

```json
{
  "id": 1,
  "short_code": "abc1234",
  "original_url": "https://example.com/long-url",
  "short_url": "http://localhost:8000/abc1234",
  "is_active": true,
  "click_count": 0,
  "created_at": "2026-03-11T12:00:00Z",
  "updated_at": "2026-03-11T12:00:00Z",
  "expires_at": null
}
```

El campo `short_url` se construye en tiempo de respuesta concatenando `settings.BASE_URL` + `/{short_code}`. Se garantiza que todos los datetimes son timezone-aware (UTC) via `model_validator`.

### URLUpdate (PATCH body)

```json
{
  "original_url": "https://new-url.com",
  "expires_at": "2027-01-01T00:00:00Z",
  "is_active": true
}
```

Todos los campos son opcionales.

### AnalyticsSummary

```json
{
  "short_code": "abc1234",
  "total_clicks": 150,
  "unique_visitors": 89,
  "browsers": { "Chrome": 80, "Firefox": 40, "Safari": 30 },
  "operating_systems": { "Windows": 70, "macOS": 50, "Linux": 30 },
  "referrers": { "google.com": 60, "twitter.com": 30, "direct": 60 },
  "clicks_by_date": { "2026-03-01": 20, "2026-03-02": 35 }
}
```

Query params opcionales: `start_date`, `end_date` (date format).

### ClickEventResponse

```json
{
  "id": 1,
  "clicked_at": "2026-03-11T15:30:00Z",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0 ...",
  "browser": "Chrome 120.0",
  "os": "Windows 10",
  "referrer": "https://google.com",
  "country": "Unknown"
}
```

### ErrorResponse

```json
{
  "detail": "URL with short code 'xyz' not found."
}
```

Todos los errores retornan un JSON con el campo `detail` describiendo la causa.

## Validation Criteria

### URL Creation

- Una URL original valida es requerida (Pydantic HttpUrl validation).
- Si se proporciona `custom_alias`, debe tener 3-30 caracteres alfanumericos (mas guiones y guiones bajos).
- Aliases que coincidan con rutas reservadas (`api`, `health`, `docs`, `redoc`, `openapi.json`, `favicon.ico`) deben ser rechazados con 422.
- Aliases duplicados deben retornar 409 Conflict.
- `expires_at` debe ser una fecha futura; fechas pasadas retornan 422.
- La creacion exitosa retorna 201 con el URLResponse completo incluyendo `short_url`.

### Redireccion

- Codigos cortos validos y activos redirigen con 307 a la URL original.
- Codigos inexistentes retornan 404.
- URLs desactivadas retornan 410 Gone.
- URLs expiradas retornan 410 Gone.
- Cada redireccion exitosa incrementa `click_count` atomicamente (`URL.click_count + 1`) y registra un `ClickEvent`.
- Si el registro de click falla, la redireccion se completa igualmente (el error se loguea y se hace rollback).

### Analytics

- El resumen de analytics muestra total de clicks, visitantes unicos (por IP distinta), distribucion de navegadores, OS, referrers, y clicks por fecha.
- Analytics de un codigo inexistente retorna 404.
- El filtrado por `start_date`/`end_date` funciona correctamente.
- Los eventos de click se paginan con `skip` y `limit`.

### QR Code

- La respuesta tiene content-type `image/png`.
- El contenido es un PNG valido (magic bytes).
- QR de un codigo inexistente retorna 404.
- El parametro `size` (1-40) modifica el tamano del QR.

### Rate Limiting

- Exceder el limite de requests retorna 429 Too Many Requests.
- `/health` siempre responde independientemente del rate limiting.

### Soft Delete

- DELETE no elimina el registro, solo establece `is_active = false`.
- La metadata de URLs desactivadas sigue accesible via GET.

## Code Summary

### Features to Files Mapping

| Feature               | Files                                                                                                          |
| --------------------- | -------------------------------------------------------------------------------------------------------------- |
| App Factory & Startup | `app/main.py`, `app/config.py`, `app/database.py`                                                              |
| URL CRUD              | `app/routers/urls.py`, `app/services/url_service.py`, `app/models/url.py`, `app/schemas/url.py`                |
| Redireccion           | `app/routers/redirect.py`, `app/services/url_service.py`, `app/services/analytics_service.py`                  |
| Click Analytics       | `app/routers/analytics.py`, `app/services/analytics_service.py`, `app/models/click.py`, `app/schemas/click.py` |
| QR Code Generation    | `app/routers/qrcode.py`, `app/services/qr_service.py`                                                          |
| Short Code Generation | `app/services/shortcode.py`                                                                                    |
| Rate Limiting         | `app/dependencies.py` (Limiter instance), aplicado en cada router                                              |
| Exception Handling    | `app/exceptions.py`                                                                                            |
| IP Extraction         | `app/utils.py`                                                                                                 |
| Database Models       | `app/models/url.py`, `app/models/click.py`                                                                     |
| Database Migrations   | `alembic/`, `alembic.ini`                                                                                      |

### Database Tables

**`urls`**: id, short_code (unique index), original_url, is_active, click_count, created_at, updated_at, expires_at

**`click_events`**: id, url_id (FK -> urls.id CASCADE), clicked_at, ip_address, user_agent, browser, os, referrer, country

## Error Codes

| HTTP Status | Causa                                                                                             |
| ----------- | ------------------------------------------------------------------------------------------------- |
| 204         | Operacion exitosa sin contenido (DELETE, favicon.ico)                                             |
| 307         | Redireccion temporal a URL original                                                               |
| 404         | Codigo corto no encontrado (`URLNotFoundException`)                                               |
| 409         | Alias personalizado ya existe (`ShortCodeExistsException`)                                        |
| 410         | URL expirada o desactivada en redireccion (`URLExpiredException`)                                 |
| 422         | Validacion fallida: URL invalida, alias invalido, fecha pasada (`InvalidURLException` / Pydantic) |
| 429         | Rate limit excedido (`RateLimitExceeded` via slowapi)                                             |

## Setup para Testing

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Ejecutar la aplicacion
uvicorn app.main:app --reload --port 8000

# La API estara en http://localhost:8000
# Docs interactivos en http://localhost:8000/docs
# ReDoc en http://localhost:8000/redoc
```

### Docker

```bash
# Build y ejecutar con docker-compose
docker-compose up --build

# O manualmente
docker build -t urlshortener .
docker run -p 8000:8000 urlshortener
```

### Variables de entorno (Settings)

| Variable           | Default                                      | Descripcion                            |
| ------------------ | -------------------------------------------- | -------------------------------------- |
| DATABASE_URL       | `sqlite+aiosqlite:///./data/urlshortener.db` | URL de conexion a la base de datos     |
| BASE_URL           | `http://localhost:8000`                      | URL base para construir URLs cortas    |
| SHORT_CODE_LENGTH  | `7`                                          | Longitud del codigo corto generado     |
| DEFAULT_RATE_LIMIT | `60/minute`                                  | Rate limit por defecto                 |
| URL_MAX_AGE_DAYS   | `null`                                       | Edad maxima de URLs en dias (opcional) |
| CORS_ORIGINS       | `["*"]`                                      | Origenes CORS permitidos               |

### Ejecutar tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=app
```

## Instrucciones para TestSprite

### Prerequisitos

1. Tener la API corriendo localmente en el puerto 8000:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. Tener TestSprite MCP Server instalado y configurado en tu IDE.

### Iniciar testing con TestSprite

Usa el siguiente prompt en tu IDE con TestSprite MCP habilitado:

```
Help me test this project with TestSprite
```

TestSprite detectara automaticamente que es un proyecto backend (FastAPI) y ejecutara su flujo de 8 pasos:

1. **Bootstrap**: Detecta el tipo de proyecto, puerto (8000), y scope.
2. **Lee este PRD**: Usa este documento como fuente de requerimientos.
3. **Analiza el codigo**: Escanea la estructura, dependencias y features.
4. **Genera PRD normalizado**: Convierte este documento a su formato JSON interno.
5. **Crea test plan**: Genera test cases categorizados (funcional, seguridad, error handling).
6. **Genera codigo de test**: Produce scripts ejecutables.
7. **Ejecuta tests**: Corre los tests en sandboxes.
8. **Reporta resultados**: Genera informe de pass/fail con recomendaciones.

### Configuracion recomendada

Si TestSprite pide parametros durante el bootstrap:

| Parametro    | Valor      |
| ------------ | ---------- |
| Project type | `backend`  |
| Port         | `8000`     |
| Test scope   | `codebase` |
| Auth needed  | No         |

### Alternativa: testing de cambios recientes

Para testear solo cambios recientes en lugar de todo el codebase:

```
Help me test my recent changes with TestSprite using diff scope
```

Esto analizara solo los archivos modificados segun git diff.
