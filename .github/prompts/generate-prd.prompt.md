---
description: "Genera un PRD (Product Requirements Document) completo para el estado actual de la aplicación. Analiza código fuente, endpoints, modelos, schemas y configuración para documentar la aplicación tal como está implementada. Escribe el resultado directamente en prd.md."
agent: "agent"
tools: ["search", "codebase", "editFiles"]
---

Genera un **PRD (Product Requirements Document)** completo y preciso para el estado actual de esta aplicación analizando el código fuente y **escríbelo directamente en el archivo `prd.md`** en la raíz del proyecto.

## Instrucciones

1. **Explorar la estructura del proyecto**: Identifica el framework, lenguaje, dependencias y arquitectura.

2. **Analizar los siguientes componentes** leyendo los archivos fuente:
   - Entry point y configuración de la aplicación
   - Modelos de base de datos (tablas, columnas, relaciones, índices)
   - Schemas de validación (request/response)
   - Rutas/Endpoints (método HTTP, ruta, status codes, rate limits)
   - Servicios y lógica de negocio
   - Manejo de errores y excepciones
   - Middleware y dependencias (auth, rate limiting, etc.)

3. **Generar el PRD** con las siguientes secciones en Markdown:

### Secciones requeridas

- **Meta**: Tabla con nombre del proyecto, versión, fecha, tipo, puerto, scope
- **Product Overview**: Descripción concisa de qué hace la aplicación y cómo
- **Core Goals**: Lista de objetivos principales del producto
- **Key Features**: Features implementadas con descripción detallada
- **Tech Stack**: Tabla de componentes y tecnologías usadas
- **User Flow Summary**: Flujo paso a paso de uso típico
- **API Endpoints**: Tablas organizadas por dominio (método, ruta, rate limit, status, descripción)
- **Request/Response Schemas**: Ejemplos JSON de cada schema con descripción de campos
- **Validation Criteria**: Reglas de validación agrupadas por feature
- **Code Summary**: Mapeo de features a archivos y descripción de tablas de BD
- **Error Codes**: Tabla de códigos HTTP y sus causas
- **Setup para Testing**: Comandos necesarios para ejecutar la aplicación

## Salida

Una vez generado el contenido del PRD:

1. **Lee el archivo `prd.md`** en la raíz del proyecto para verificar si ya existe.
2. **Reemplaza todo el contenido** del archivo `prd.md` con el PRD generado. Si el archivo no existe, créalo.
3. **Confirma** al usuario que el archivo fue actualizado exitosamente.

## Reglas

- Documenta SOLO lo que está implementado en el código, no lo que debería estar.
- Usa español para las descripciones.
- Los ejemplos JSON deben reflejar los schemas reales del código.
- Incluye todos los status codes que cada endpoint puede retornar.
- Documenta los rate limits exactos si existen.
- El resultado DEBE escribirse directamente en el archivo `prd.md` en la raíz del proyecto, no solo mostrarse en el chat.
