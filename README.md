# Chatbot técnico en español (FastAPI + React)

Este repositorio contiene un scaffold completo para un chatbot conversacional en español orientado a profesionales de programación y ciberseguridad. Incluye:

- Backend: `FastAPI` con autenticación JWT, endpoints de chat, historial, moderación básica usando la API de OpenAI y persistencia mínima con `SQLModel` (SQLite por defecto).
- Frontend: `React` (Vite) con pantalla de login/registro, chat y resaltado simple de código.
- Contenedores: `Dockerfile` para desarrollo, `Dockerfile.prod` para frontend con Caddy (TLS automático) y `docker-compose`/`docker-compose.prod.yml` para ejecutar localmente o en producción.

Contenido del repositorio
- `backend/` — código del servidor FastAPI.
- `frontend/` — aplicación React (Vite).
- `docker-compose.yml` — orquesta servicios para desarrollo.
- `docker-compose.prod.yml` — orquesta servicios para producción (frontend servido por Caddy).
- `ARCHITECTURE.md` — diseño de arquitectura y decisiones clave.
- `DELIVERY.md` — resumen de entrega y pasos para revisión.

Requisitos previos
- Docker y Docker Compose (para correr los contenedores).
- Cuenta de OpenAI y `OPENAI_API_KEY` (se usa `ChatCompletion` y `Moderation`).
- (Opcional) `node` y `npm` si deseas correr frontend localmente sin Docker.

Variables de entorno
Crear un archivo `backend/.env` (puedes copiar `backend/.env.example`) y definir al menos:

- `OPENAI_API_KEY` — tu clave de OpenAI.
- `SECRET_KEY` — cadena aleatoria para firmar JWT.
- `DATABASE_URL` — por defecto `sqlite:///./database.db`.
- `ACCESS_TOKEN_EXPIRE_MINUTES` — duración del token (opcional).

Desarrollo local (rápido)

1) Copiar ejemplo de variables de entorno:

```powershell
copy backend\.env.example backend\.env
rem editar backend\.env y poner OPENAI_API_KEY y SECRET_KEY
```

2) Levantar servicios en modo desarrollo:

```powershell
docker-compose up --build
```

3) Acceder:

- Frontend: http://localhost:5173
- API Swagger: http://localhost:8000/docs

Endpoints principales

- `POST /auth/register` — registrar usuario (params: `username`, `password`).
- `POST /auth/token` — obtener token (OAuth2 password flow).
- `POST /chat` — enviar mensaje al chatbot (Bearer token). Payload: `{ "message": "..." }`.
- `GET /history` — obtener historial del usuario (Bearer token).
- `POST /history/clear` — borrar historial del usuario (Bearer token).

Ejemplo de uso con `curl` (login y chat)

```bash
# Registrar (si no existe):
curl -X POST "http://localhost:8000/auth/register?username=test&password=secret"

# Obtener token:
curl -X POST -d "username=test&password=secret" http://localhost:8000/auth/token

# Suponiendo que obtienes access_token=XYZ, enviar chat:
curl -X POST http://localhost:8000/chat -H "Authorization: Bearer XYZ" -H "Content-Type: application/json" -d '{"message":"Explícame cómo funciona XSS con ejemplo de código"}'
```

Despliegue en producción (local con Docker)

1) Construir y levantar (frontend servido por Caddy con TLS automático):

```powershell
docker-compose -f docker-compose.prod.yml up --build -d
```

2) Acceder al servicio en https://chat.data-shark.com (API en https://chat.data-shark.com/api; la ruta `/api/` está proxyada desde el frontend en Caddy).

Recomendaciones de seguridad y operación

- No uses SQLite en producción; cambia `DATABASE_URL` por PostgreSQL o similar.
- Usa un `SECRET_KEY` fuerte y guarda las variables de entorno en un sistema seguro.
- Habilita TLS/HTTPS en el proxy inverso (Nginx) y gestiona certificados (Let's Encrypt).
- Añade rate-limiting persistente (Redis) para evitar abusos; actualmente hay un limitador en memoria para desarrollo.
- Revisa y ajusta la política de moderación (`ARCHITECTURE.md` y `backend/app/main.py`).

Pruebas

- No se incluyeron tests automatizados en este scaffold; se recomienda añadir tests unitarios para los endpoints (`/chat`, moderación) y pruebas de integración para el flujo completo.

Contribuir

Si quieres mejorar este proyecto, crea una rama nueva, realiza cambios y abre un pull request. Sugerencias inmediatas:

- Añadir tests y CI (GitHub Actions).
- Integrar Vector DB para memoria a largo plazo.
- Reemplazar el limitador in-memory por Redis y añadir métricas.

Soporte y contacto

Si quieres que continúe con alguno de los puntos siguientes (tests, TLS, despliegue en un proveedor específico), dime cuál y lo implemento.


Despliegue de producción

1) Construir y levantar en modo producción (servirá frontend con Caddy y TLS automático):

```powershell
docker-compose -f docker-compose.prod.yml up --build -d
```

2) Acceder al servicio en https://chat.data-shark.com (API en https://chat.data-shark.com/api; la ruta `/api/` está proxyada desde el frontend).

Notas de producción:
- Recomendado: configurar `backend/.env` con `DATABASE_URL` a una DB más robusta (Postgres) y `SECRET_KEY` fuerte.
- Asegurar que los registros DNS apunten `chat.data-shark.com` a la IP del servidor y que los puertos 80/443 estén abiertos (Caddy gestionará certificados automáticamente).
- Revisar límites de la API de OpenAI y configurar billing/alertas.
