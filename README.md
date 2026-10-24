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
| [`conocimiento/base_cmc.md`](conocimiento/base_cmc.md) | **Preliminar** de la base de conocimiento: 47 profesionales con especialidad, edades, días, cómo se piden los turnos, obras sociales y aranceles. Se pega dentro del prompt. |
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
- Medios de pago y qué traer el día del turno
- Los `[COMPLETAR]` y `[CONFIRMAR]` de `conocimiento/base_cmc.md`

## Fuentes de la base de conocimiento

Se armó con "Resumen médicos y O.S. que atienden" (04/2026), "Arancel particular consultas médicas" (05/2026) y "Arancel particular de prestaciones diferentes" (05/2026). Se dejó afuera, a propósito, todo dato interno: CUIT, matrículas, celulares, emails, alias y cuentas bancarias, porcentajes de alquiler, por dónde se factura cada obra social y usuarios y contraseñas de portales. Tampoco se usaron el detalle de alquileres 2024 (es información financiera interna) ni los aranceles OSDE de ecografías (son valores que paga OSDE al prestador, no lo que abona el paciente).

## Puntos a confirmar

1. **Texto del mensaje fijo clínico.** La propuesta incluye la indicación de llamar a emergencias o ir a la guardia, y el link para pedir turno. Revisarlo desde el criterio médico antes de activar.
2. **Mensajes mixtos** (clínico + administrativo): el prompt manda primero el mensaje fijo completo y después responde solo la parte administrativa, sin mencionar los síntomas. Si prefieren que ante cualquier componente clínico salga *únicamente* el mensaje fijo, es un cambio de una línea.
3. **Base de conocimiento (preliminar):**
   - **Vigencia de los aranceles:** son de mayo de 2026. Actualizarlos antes de activar el bot.
   - **Columna "PAMI"** de la planilla de consultas: se interpretó como el valor que abona un afiliado PAMI. Confirmar.
   - **"Arancel diferenciado"** (no prestador), **"arancel hospitalario (el general)"** y **"arancel compensatorio"**: ¿el bot debe informar montos o solo derivar a recepción? Hoy deriva.
   - **Profesionales que dan sus propios turnos** (Dañiluk, Luraschi, Rossiter, Rial, Tanga, Crugnale, Tuzio, Hary): ¿el bot puede compartir su celular? Hoy no lo comparte y deriva a recepción.
   - **Dra. Manuela Castro:** el documento dice que sus turnos van por "Treelan", no por Dr. App.
   - **Diferencias entre documentos:** consulta odontológica $40.000 (Word) vs. $50.000 (planilla 03/2026; se usó $50.000); Dra. Rossi figura como Clínica médica en 2026 y como Diabetología en 2024; Dr. Verón con "Austral Salud????"; la Lic. Cortinovis no tiene lista de obras sociales, pero la planilla sugiere OSDE.
   - **Profesionales en la planilla de aranceles que no están en el Word** (Dra. Dimilito, Oftalmología infantil): no se incluyeron. ¿Siguen atendiendo?
   - **Faltan aranceles de:** ecografías (Dr. Chomont), estudios audiológicos, electroencefalogramas infantiles, medicina estética y prácticas cardiológicas.
   - **Urgencias odontológicas:** el Word indica dar el Instagram de la Dra. Hvala a pacientes con dolor. Para el bot es una consulta clínica (mensaje fijo), así que no se incluyó.
   - **Días de atención:** solo figuran para algunos profesionales.
