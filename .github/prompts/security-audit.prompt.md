---
description: "Audita el repositorio en busca de secretos expuestos, rutas sin protección y validaciones faltantes"
name: "Security Audit"
argument-hint: "Ruta o alcance opcional (por ejemplo: app/, tests/, todo el repo)"
agent: "agent"
---

Realiza una auditoria de seguridad del alcance indicado (si no se indica, usa todo el repositorio) y enfocate en:

1. Secretos o API keys expuestos.
2. Rutas sin autenticacion/autorizacion.
3. Falta de controles de acceso por recurso.
4. Entradas no sanitizadas o no validadas (body, query, path, headers).
5. Riesgos de inyeccion, SSRF, open redirect, path traversal y deserializacion insegura.

Requisitos de salida:

- Guarda un reporte en `security.md`.
- Ordena hallazgos por severidad: Critical, High, Medium, Low.
- Para cada hallazgo incluye: evidencia (archivo y linea), impacto y remediacion concreta.
- Incluye una seccion de "Positive Security Notes" con controles existentes.
- Si no hay hallazgos en una categoria, dilo explicitamente.
- No modifiques codigo de aplicacion, solo crea/actualiza el reporte.
