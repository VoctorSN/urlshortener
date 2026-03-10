# URL Shortener API

API completa de acortador de URLs construida con FastAPI, SQLAlchemy (async) y SQLite.

## Funcionalidades

- **Acortar URLs** con codigos cortos auto-generados o aliases personalizados
- **Redireccion** via codigos cortos (HTTP 307)
- **Analytics de clicks**: navegador, sistema operativo, referrer, IP, conteo por fecha
- **Expiracion de URLs**: configura una fecha limite para tus enlaces
- **Generacion de QR codes**: obtiene un PNG con el QR de tu URL corta
- **Rate limiting**: proteccion contra abuso por IP
- **Documentacion interactiva**: Swagger UI y ReDoc auto-generados

## Stack Tecnologico

| Componente       | Tecnologia             |
| ---------------- | ---------------------- |
| Framework        | FastAPI                |
| ORM              | SQLAlchemy 2.0 (async) |
| Base de datos    | SQLite (aiosqlite)     |
| Migraciones      | Alembic                |
| Tests            | pytest + httpx         |
| Containerizacion | Docker                 |

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

## Documentacion de la API

Una vez corriendo el servidor:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principales

| Metodo   | Ruta                         | Descripcion                 |
| -------- | ---------------------------- | --------------------------- |
| `POST`   | `/api/urls`                  | Crear URL corta             |
| `GET`    | `/api/urls`                  | Listar todas las URLs       |
| `GET`    | `/api/urls/{code}`           | Obtener metadata            |
| `PATCH`  | `/api/urls/{code}`           | Actualizar URL              |
| `DELETE` | `/api/urls/{code}`           | Desactivar URL              |
| `GET`    | `/{code}`                    | Redireccion al URL original |
| `GET`    | `/api/urls/{code}/analytics` | Resumen de analytics        |
| `GET`    | `/api/urls/{code}/clicks`    | Eventos de click            |
| `GET`    | `/api/urls/{code}/qr`        | QR code en PNG              |
| `GET`    | `/health`                    | Health check                |

### Ejemplo de Uso

```bash
# Crear una URL corta
curl -X POST http://localhost:8000/api/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.ejemplo.com/pagina-muy-larga"}'

# Crear con alias personalizado
curl -X POST http://localhost:8000/api/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.ejemplo.com", "custom_alias": "mi-link"}'

# Ver analytics
curl http://localhost:8000/api/urls/mi-link/analytics

# Descargar QR code
curl -o qr.png http://localhost:8000/api/urls/mi-link/qr
```

## Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Test especifico
pytest tests/test_urls.py -v
```

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

## Variables de Entorno

| Variable             | Default                                      | Descripcion                      |
| -------------------- | -------------------------------------------- | -------------------------------- |
| `DATABASE_URL`       | `sqlite+aiosqlite:///./data/urlshortener.db` | URL de la base de datos          |
| `BASE_URL`           | `http://localhost:8000`                      | URL base publica                 |
| `SHORT_CODE_LENGTH`  | `7`                                          | Longitud de codigos generados    |
| `DEFAULT_RATE_LIMIT` | `60/minute`                                  | Limite de peticiones por defecto |
| `URL_MAX_AGE_DAYS`   | 1                                            | Expiracion por defecto en dias   |
| `CORS_ORIGINS`       | `["*"]`                                      | Origenes CORS permitidos         |
