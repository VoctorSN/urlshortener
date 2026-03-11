---
description: "Genera tests de API basados en el PRD. Analiza prd.md y el código fuente para crear tests pytest+httpx que cubran todos los endpoints, validaciones y casos edge documentados."
agent: "agent"
tools: ["search", "codebase"]
---

Genera **tests completos de la API** basándote en el documento [prd.md](../../prd.md) y los patrones de test existentes en el proyecto.

## Proceso

1. **Leer el PRD** (`prd.md` en la raíz) para extraer:
   - Todos los endpoints (método, ruta, status codes esperados)
   - Schemas de request/response (campos, tipos, valores válidos/inválidos)
   - Criterios de validación (reglas de negocio, error codes)
   - Casos edge documentados (expiración, soft-delete, rate limiting, rutas reservadas)

2. **Leer los tests existentes** en `tests/` para entender:
   - Estructura de fixtures (`conftest.py`): client async, db_session, sample_url
   - Estilo: clases con `@pytest.mark.asyncio`, métodos `async def test_*`
   - Cómo se usa `httpx.AsyncClient` con `follow_redirects=False` para redirects
   - Cómo se manipula la BD directamente para tests de expiración

3. **Generar tests** que cubran cada sección del PRD:

### Tests requeridos por dominio

#### URL CRUD (`test_urls.py`)
- POST `/api/urls` — creación exitosa (201), con alias (201), alias duplicado (409), URL inválida (422), alias reservado (422), alias inválido formato (422), con expiración futura (201), con expiración pasada (422)
- GET `/api/urls` — lista vacía (200), con paginación skip/limit (200)
- GET `/api/urls/{code}` — encontrado (200), no encontrado (404), campos del schema completos
- PATCH `/api/urls/{code}` — actualizar URL (200), actualizar expiración (200), no encontrado (404)
- DELETE `/api/urls/{code}` — soft delete (204), verificar `is_active=false`, metadata accesible post-delete

#### Redirección (`test_redirect.py`)
- GET `/{short_code}` — redirect 307, header Location correcto, código no encontrado (404), URL inactiva (410), URL expirada (410), incremento de click_count

#### Analytics (`test_analytics.py`)
- GET `/api/urls/{code}/analytics` — summary vacío (200), con clicks (200), no encontrado (404), filtrado por fechas
- GET `/api/urls/{code}/clicks` — paginación, campos del evento (browser, os, referrer, ip_address)

#### QR Code (`test_qrcode.py`)
- GET `/api/urls/{code}/qr` — content-type image/png, PNG magic bytes válidos, no encontrado (404), parámetro size

#### Health (`test_health.py`)
- GET `/health` — status 200, body `{"status":"healthy"}`

#### Rate Limiting (`test_rate_limiting.py`)
- Requests dentro del límite pasan
- Health no tiene rate limit

#### Services (`test_services.py`)
- `generate_short_code()` — longitud, unicidad, caracteres URL-safe
- `is_valid_custom_alias()` — válidos, cortos, largos, caracteres inválidos, reservados
- `generate_qr_code()` — bytes PNG válidos, tamaño configurable
- `parse_user_agent()` — parsing de navegador y OS

## Reglas

- Usa **pytest + pytest-asyncio + httpx** (AsyncClient con ASGITransport)
- Reutiliza las fixtures de `conftest.py`: `client`, `db_session`, `sample_url`
- Para tests de expiración: crea la URL vía API, luego modifica `expires_at` en la BD directamente
- Usa `follow_redirects=False` en tests de redirección
- Verifica tanto status codes como campos del body de respuesta
- No uses mocks — todos los tests son de integración contra la app ASGI en memoria
- Cada archivo de test debe ser autocontenido con sus imports
- Agrupa tests en clases por feature con `@pytest.mark.asyncio`
- Valida contra los schemas exactos documentados en el PRD (campos requeridos, tipos)

## Cobertura de código

Después de generar los tests, ejecuta el suite completo con cobertura:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html tests/
```

Analiza el reporte de cobertura para:

1. **Identificar código muerto** (líneas/funciones con 0% cobertura que ningún test ni flujo de la app usa).
2. **Identificar ramas no cubiertas** (bloques `if/else`, `except`, early returns sin test).
3. **Añadir tests adicionales** para cubrir las ramas faltantes detectadas en el reporte.
4. **Proponer eliminar código muerto** que no sea alcanzable por ningún flujo documentado en el PRD.

El objetivo es alcanzar **≥90% de cobertura** en el paquete `app/`, priorizando:
- Todos los handlers de error y excepciones personalizadas
- Todas las ramas de validación en servicios
- Flujos alternativos (URL expirada, inactiva, alias duplicado, etc.)
- Utilidades (`utils.py`, `dependencies.py`, `config.py`)
