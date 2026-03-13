# URL Shortener API

API completa de acortador de URLs construida con FastAPI, SQLAlchemy (async) y PostgreSQL.

## Funcionalidades

- **Acortar URLs** con codigos cortos auto-generados o aliases personalizados
- **Redireccion** via codigos cortos (HTTP 307)
- **Analytics de clicks**: navegador, sistema operativo, referrer, IP, conteo por fecha
- **Expiracion de URLs**: configura una fecha limite para tus enlaces
- **Generacion de QR codes**: obtiene un PNG con el QR de tu URL corta
- **Rate limiting**: proteccion contra abuso por IP
- **Documentacion interactiva**: Swagger UI y ReDoc auto-generados

## Stack Tecnologico

| Componente       | Tecnologia                      |
| ---------------- | ------------------------------- |
| Framework        | FastAPI                         |
| ORM              | SQLAlchemy 2.0 (async)          |
| Base de datos    | PostgreSQL (asyncpg)            |
| Migraciones      | Alembic                         |
| Tests            | pytest + pytest-asyncio + httpx |
| Containerizacion | Docker + Docker Compose         |

## Inicio Rapido

### Con Docker (recomendado)

```bash
# Clonar el repositorio
git clone <repo-url>
cd urlshortener

# Levantar la aplicacion con PostgreSQL
docker compose up --build
```

Esto levanta dos contenedores:

- **`urlshortener-db`**: PostgreSQL 16 con los datos persistidos en un volumen.
- **`urlshortener-api`**: La API en el puerto 8000. Las migraciones se ejecutan automaticamente al iniciar.

La API estara disponible en `http://localhost:8000`.

### Instalacion local (desarrollo)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias (incluye dev)
pip install -e ".[dev]"

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu conexion a PostgreSQL

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

> **Nota**: Necesitas una instancia de PostgreSQL corriendo. Puedes levantar solo la base de datos con:
>
> ```bash
> docker compose up db
> ```
>
> Y usar `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener` en tu `.env`.

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

Los tests usan una base de datos SQLite en memoria (via `aiosqlite`), por lo que **no necesitas PostgreSQL** para ejecutarlos.

```bash
# Activar el entorno virtual
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias de desarrollo (si no lo hiciste antes)
pip install -e ".[dev]"

# Ejecutar todos los tests
pytest

# Con output detallado
pytest -v

# Con coverage
pytest --cov=app --cov-report=term-missing

# Un archivo de test especifico
pytest tests/test_urls.py -v
```

> Los warnings de dependencias externas estan filtrados en `pyproject.toml` (`[tool.pytest.ini_options]`), por lo que la salida de los tests es limpia.

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

| Variable             | Default                                                              | Descripcion                      |
| -------------------- | -------------------------------------------------------------------- | -------------------------------- |
| `DATABASE_URL`       | `postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener` | URL de conexion a PostgreSQL     |
| `BASE_URL`           | `http://localhost:8000`                                              | URL base publica                 |
| `SHORT_CODE_LENGTH`  | `7`                                                                  | Longitud de codigos generados    |
| `DEFAULT_RATE_LIMIT` | `60/minute`                                                          | Limite de peticiones por defecto |
| `URL_MAX_AGE_DAYS`   | `1`                                                                  | Expiracion por defecto en dias   |
| `CORS_ORIGINS`       | `["*"]`                                                              | Origenes CORS permitidos         |

## Configuracion de PostgreSQL

### Con Docker Compose (sin configuracion manual)

Al ejecutar `docker compose up --build`, el servicio `db` crea automaticamente la base de datos `urlshortener` con usuario `postgres` y contraseña `postgres`. La API se conecta internamente usando:

```
postgresql+asyncpg://postgres:postgres@db:5432/urlshortener
```

No necesitas instalar ni configurar nada adicional.

### PostgreSQL local

Si prefieres usar una instancia de PostgreSQL instalada en tu maquina:

1. **Crear la base de datos**:

   ```sql
   CREATE DATABASE urlshortener;
   ```

2. **Configurar la conexion** en el archivo `.env`:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://<usuario>:<contraseña>@localhost:5432/urlshortener
   ```

   Ejemplo con los valores por defecto:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener
   ```

3. **Ejecutar las migraciones** para crear las tablas:

   ```bash
   alembic upgrade head
   ```

### Solo la base de datos con Docker

Si quieres desarrollar localmente pero no instalar PostgreSQL, puedes levantar unicamente el contenedor de la base de datos:

```bash
docker compose up db
```

Esto expone PostgreSQL en `localhost:5432`. Usa esta `DATABASE_URL` en tu `.env`:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener
```

### Formato de DATABASE_URL

La URL de conexion sigue el formato:

```
postgresql+asyncpg://<usuario>:<contraseña>@<host>:<puerto>/<base_de_datos>
```

| Parte          | Descripcion                        | Default        |
| -------------- | ---------------------------------- | -------------- |
| `usuario`      | Usuario de PostgreSQL              | `postgres`     |
| `contraseña`   | Contraseña del usuario             | `postgres`     |
| `host`         | Host donde corre PostgreSQL        | `localhost`    |
| `puerto`       | Puerto de PostgreSQL               | `5432`         |
| `base_de_datos`| Nombre de la base de datos         | `urlshortener` |
