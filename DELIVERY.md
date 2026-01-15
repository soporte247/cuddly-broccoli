# Entrega / Resumen del paquete

Este repositorio contiene un scaffold funcional para un chatbot técnico en español. A continuación se resume qué incluye, cómo probar y próximos pasos recomendados.

Archivos y carpetas principales
- `backend/` — servidor FastAPI con:
  - `app/main.py` — lógica de autenticación, endpoints de chat, moderación básica, historial y limitador simple.
  - `.env.example` — variables de entorno necesarias.
  - `requirements.txt`, `Dockerfile` — dependencias y contenedor.
- `frontend/` — app React (Vite) con:
  - `src/` — componentes `App.jsx`, `components/Chat.jsx`, estilos.
  - `Dockerfile` (dev) y `Dockerfile.prod` (producción con Nginx).
- `docker-compose.yml` — orquesta frontend/backend para desarrollo.
- `docker-compose.prod.yml` — orquesta servicios para producción (frontend servido por Nginx en el puerto 80).
- `ARCHITECTURE.md` — diseño de arquitectura y decisiones técnicas.
- `README.md` — documentación de uso y despliegue.

Cómo probar rápidamente

1) Copia variables de entorno:

```powershell
copy backend\.env.example backend\.env
# editar backend\.env -> OPENAI_API_KEY y SECRET_KEY
```

2) Levantar en modo desarrollo:

```powershell
docker-compose up --build
```

3) Acceder al frontend en http://localhost:5173 y al Swagger del backend en http://localhost:8000/docs

Checklist de entrega
- [x] Scaffold backend y frontend
- [x] Autenticación JWT y endpoints básicos
- [x] Integración con OpenAI ChatCompletion y Moderation (requiere clave)
- [x] Rate limiter in-memory y persistencia mínima de mensajes (SQLite)
- [x] Docker + docker-compose (dev y prod)
- [x] Documentación básica y arquitectura

Limitaciones conocidas

- No hay tests automatizados incluidos.
- Rate-limiter en memoria (no persistente) — sustituir por Redis en producción.
- Política de moderación básica; puede requerir ajustes según el uso.

Próximos pasos recomendados

1. Añadir pruebas unitarias y de integración.
2. Sustituir SQLite por PostgreSQL para producción.
3. Configurar Redis para rate-limiting y caching.
4. Añadir métricas y logging centralizado (Prometheus / ELK).
5. Preparar despliegue en la nube (DigitalOcean, AWS, GCP) con TLS.
