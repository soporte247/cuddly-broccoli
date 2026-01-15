# Política de seguridad y moderación

Este documento describe las reglas y procesos que aplica el chatbot para garantizar un uso seguro y responsable.

Objetivos
- Evitar la generación o facilitación de actividades ilegales o dañinas.
- Permitir contenido técnico legítimo para profesionales (explicaciones, ejemplos seguros de código) siempre que no promueva abuso.
- Facilitar mecanismos de moderación y reporte de contenidos problemáticos.

Reglas principales
- Contenido prohibido: instrucciones para cometer delitos (exploit activo, creación/distribución de malware, ataques DDoS, evasión de sistemas de seguridad, ingeniería social maliciosa, etc.).
- Contenido restringido: ejemplos que puedan facilitar ataques si no se contextualizan con mitigaciones y responsabilidad. El asistente debe incluir advertencias y no proveer pasos accionables que causen daño.
- Contenido permitido: explicaciones teóricas, mejores prácticas de seguridad, análisis de vulnerabilidades a nivel conceptual, y ejemplos de código seguros y educativos.

Proceso de moderación
- Entrada del usuario:
  1. Comprobación local rápida (denylist y patrones regex configurables).
  2. Moderación externa (OpenAI Moderation API) si está disponible.
  3. Si cualquiera de los pasos marca el contenido como prohibido, la petición se rechaza con código HTTP 403 y se registra el evento.

- Respuesta del asistente:
  1. Tras recibir la respuesta del LLM, se aplica una comprobación local.
  2. Si la respuesta infringe la política, se bloquea la respuesta y se devuelve un mensaje genérico explicando que la respuesta ha sido bloqueada por seguridad.

Reporte y apelación
- Los usuarios pueden reportar mensajes problemáticos mediante el endpoint `/report` (autenticado). Los reportes se almacenan para revisión manual.
- Proceso de apelación: se sugiere mantener un procedimiento manual de revisión (no automatizado) donde un administrador revise los reportes y decida reponer o ajustar las políticas.

Limitación de uso y throttling
- Aplicar rate-limiting por usuario para prevenir abuso y proteger costos de API.
- Limitar longitud de prompts y número de tokens en respuestas para minimizar exposiciones accidentales.

Responsabilidad y disclaimers
- El servicio está destinado a uso profesional y educativo. No se debe utilizar para actividades ilegales.
- Los administradores deben revisar y adaptar las reglas locales y las listas de denylist conforme cambie el contexto de uso.

Configuración
- `backend/app/policies.py` contiene patrones denylist iniciales y funciones de comprobación.
- Ajusta y amplía `DENY_PATTERNS` y reglas según necesidades y jurisdicción.
