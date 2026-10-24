# Chatbot de WhatsApp — CMCardales

Asistente virtual de WhatsApp para CMCardales. Arquitectura: **WhatsApp Cloud API (número nuevo dedicado) → Make.com → Anthropic Claude → respuesta por WhatsApp.**

## Alcance v1

- Información general del centro (dirección, horarios, especialidades, obras sociales, preparación de estudios).
- Orientar para sacar, cambiar o cancelar turnos (link de Dr. App / teléfono). El bot **no** agenda ni ve la agenda.
- **Regla de seguridad clínica:** ante cualquier consulta clínica, incluidas posibles urgencias, responde solo con un mensaje fijo y nunca la deriva a una persona.
- Fuera de alcance por ahora: agendar turnos, recordatorios (los manda Dr. App por email) y la derivación automática a humano. Para temas administrativos que no puede resolver, indica el contacto de recepción.

## Archivos

| Archivo | Para qué |
|---|---|
| [`prompts/system_prompt.md`](prompts/system_prompt.md) | El system prompt que se pega en el módulo Anthropic Claude de Make.com. |
| [`prompts/casos_de_prueba.md`](prompts/casos_de_prueba.md) | Casos para validar el bot antes de salir a producción (los clínicos son excluyentes). |

## Cómo usarlo en Make.com

1. Completar todos los `[COMPLETAR: ...]` del prompt (lista abajo).
2. En el escenario del centro (con la conexión de WhatsApp de **CMCardales**, no la del consultorio de Alan), en el módulo Anthropic Claude → *Create a Message*:
   - **System prompt:** el texto entre las líneas `=====`.
   - **Messages:** el historial reciente de la conversación (idealmente los últimos 10 mensajes), para que el bot tenga contexto.
   - **Max tokens:** 500 alcanza para mensajes de WhatsApp.
3. Correr todos los casos de prueba y anotar los resultados.

## Datos a completar

- Nombre institucional completo
- Dirección y link de Google Maps; cómo llegar / estacionamiento (opcional)
- Horario de atención del centro
- Teléfono / WhatsApp de recepción y su horario
- Email (opcional)
- Guardia: si hay o no
- **Número de emergencias de la zona** (va en el mensaje fijo clínico)
- Link de turnos de Dr. App e instrucciones para sacar, cambiar y cancelar turnos
- Especialidades, profesionales y días de atención
- Estudios y prácticas, con su preparación
- Obras sociales y prepagas (autorizaciones, bonos, copagos)
- Atención particular y medios de pago
- Qué traer el día del turno

## Puntos a confirmar

1. **Texto del mensaje fijo clínico.** La propuesta incluye la indicación de llamar a emergencias o ir a la guardia, y el link para pedir turno. Revisarlo desde el criterio médico antes de activar.
2. **Mensajes mixtos** (clínico + administrativo): el prompt manda primero el mensaje fijo completo y después responde solo la parte administrativa, sin mencionar los síntomas. Si prefieren que ante cualquier componente clínico salga *únicamente* el mensaje fijo, es un cambio de una línea.
