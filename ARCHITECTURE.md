# Diseño de arquitectura — Chatbot técnico (ES)

Resumen rápido
- Objetivo: servicio web que ofrece un chatbot en español para profesionales de programación y ciberseguridad, con respuestas técnicas y ejemplos de código, moderación y autenticación de usuarios.

Componentes principales
- Frontend (React/Vite): interfaz de chat, login/registro, resaltado de código, historial de conversaciones en memoria del cliente.
- Backend (FastAPI): autenticación JWT, endpoints REST (`/auth/register`, `/auth/token`, `/chat`), orquestación de prompts, llamadas a OpenAI (ChatCompletion y Moderation), validación y logging.
- Persistencia ligera: SQLite mediante `sqlmodel` para usuarios (registro y credenciales). Opcional: añadir vector DB (Milvus, FAISS, Weaviate) para memoria/knowledge base.
- Moderación: usar OpenAI Moderation API antes de enviar prompts y aplicar reglas locales (denylist/allowlist). Registrar incidentes en logs.
- Infraestructura / despliegue: contenedores Docker para `frontend` y `backend`; `docker-compose` para desarrollo. En producción, servir frontend compilado con Nginx y backend con Uvicorn/Gunicorn detrás de un proxy (NGINX).

Flujo de datos (petición de chat)
1. El usuario en el frontend envía mensaje (requiere token Bearer).
2. Frontend hace POST a `/chat` con Authorization header.
3. Backend valida token (JWT) y obtiene el usuario.
4. Backend ejecuta moderación del texto con OpenAI Moderation. Si está marcado, devuelve 403 y registra el evento.
5. Si pasa moderación, backend construye prompt (system + user + contexto breve).
6. Backend llama a OpenAI ChatCompletion (o el proveedor configurado) y recibe respuesta.
7. Backend puede aplicar post-procesamiento (formato de código, sanitización, advertencias de seguridad) y devolver la respuesta al frontend.
8. Opcional: indexar pares (prompt, respuesta) en la vector DB para contexto futuro.

Gestión del contexto y memoria
- Modo por sesión: almacenar últimos N mensajes en memoria (o DB) para mantener contexto corto en la conversación.
- Modo persistente (opcional): usar vector DB para buscar documentos relevantes (knowledge base) y anexarlos al prompt. Control de privacidad y consentimiento es esencial.

Seguridad y moderación
- Moderación previa: OpenAI Moderation API o reglas locales (expresiones regulares, denylists).
- Políticas: bloquear instrucciones para actividades ilegales/delictivas; permitir contenido técnico seguro y educativo con disclaimers.
- Autenticación: JWT con `SECRET_KEY`, expiración configurable; endpoints `/auth/register` y `/auth/token`.
- Rate limiting (recomendado): aplicar límites por usuario/IP para evitar abuso (ej. 60 requests/min por usuario). Implementar con Redis o middleware.
- Registro y auditoría: almacenar logs de requests, respuestas rechazadas por moderación y errores. Mantener políticas de retención y acceso restringido.

Privacidad y datos
- Evitar almacenar prompts completos si contienen información sensible, a menos que el usuario consienta.
- Cifrado en tránsito (HTTPS) y recomendaciones para producción: usar certificados TLS en el proxy reverso.

Escalabilidad
- Inicial: contenedores monolíticos con PostgreSQL o SQLite para pruebas.
- Intermedio: separar servicios, usar una base de datos gestionada, añadir Redis para caching y rate-limiting.
- Avanzado: despliegue en Kubernetes, autoscaling, vector DB gestionada y colas (RabbitMQ/Kafka) para orquestar lotes de peticiones y jobs de indexado.

Observabilidad
- Métricas: latencia de llamada a OpenAI, tasa de errores, número de solicitudes por usuario.
- Logs centralizados (ELK/CloudWatch) y alertas para fallos críticos.

Endpoints principales (propuesta)
- POST `/auth/register` — registrar usuario (username, password)
- POST `/auth/token` — obtener token (OAuth2 Password flow)
- POST `/chat` — enviar mensaje al chatbot (Bearer token) -> { reply }
- GET `/health` — estado del servicio

Decisiones clave y justificantes
- OpenAI API: facilita respuestas de alta calidad y moderación integrada; requiere gestionar costos.
- FastAPI: rendimiento, tipado y documentación automática (Swagger).
- React + Vite: interfaz rápida y fácil de desarrollar.
- Docker Compose: desarrollo y pruebas locales simples; producción debe usar contenedores optimizados.

Próximos pasos técnicos inmediatos
- Implementar rate limiting y logging estructurado en `backend/app/main.py`.
- Añadir pruebas básicas para el endpoint `/chat` y para la lógica de moderación.
- Preparar build de producción del frontend y configuración de Nginx.
