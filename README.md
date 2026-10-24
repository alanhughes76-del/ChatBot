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
| [`prompts/system_prompt.md`](prompts/system_prompt.md) | Reglas del bot: alcance, regla de seguridad clínica, tono y datos generales del centro. |
| [`conocimiento/base_cmc.md`](conocimiento/base_cmc.md) | Base de conocimiento: 46 profesionales con especialidad, edades, días, cómo se piden los turnos, obras sociales y aranceles. |
| [`make/system_prompt_completo.txt`](make/system_prompt_completo.txt) | El prompt con la base ya integrada: **es lo que se pega en Make**. |
| [`make/escenario_cmc.blueprint.json`](make/escenario_cmc.blueprint.json) | El escenario de Make (también importable con *Import Blueprint*). |
| [`make/build_blueprint.py`](make/build_blueprint.py) | Regenera los dos archivos anteriores: `python3 make/build_blueprint.py`. Correrlo cada vez que cambien el prompt o la base. |
| [`prompts/casos_de_prueba.md`](prompts/casos_de_prueba.md) | Casos para validar el bot antes de salir a producción (los clínicos son excluyentes). |

## Escenario de Make: "CMCardales — Bot de WhatsApp"

Ya está creado en el team "My Team" de Make, **inactivo** (id 6763454). Usa el data store "CMCardales - Historial de conversaciones", que ahora tiene estructura (historial, último mensaje y nombre de perfil).

**Cómo funciona**
1. **Mensaje entrante:** llega un mensaje al número de WhatsApp de CMCardales.
2. **Router:**
   - **Mensaje de texto:**
     - Lee el historial de esa persona. Si pasaron más de 24 h desde su último mensaje, arranca de cero.
     - Claude responde con el prompt completo.
     - La respuesta se envía por WhatsApp.
     - Se guarda el historial actualizado (los últimos 3.000 caracteres).
   - **Audio, imagen u otro:** responde que por ahora solo lee texto, con el teléfono de recepción y el 107.
3. **Si Claude falla:** se envía un aviso con el teléfono de recepción y el 107, y la ejecución termina sin error.

**Lo que falta para activarlo (en Make, a mano)**
1. **Conexión de WhatsApp de CMCardales:** crearla con el número nuevo (no la de tu consultorio). En el módulo "Mensaje entrante", crear el webhook con esa conexión. En los tres módulos de envío ("Responder por WhatsApp", "Aviso si Claude falla" y "Aviso: solo texto"), elegir la conexión. El *Sender ID* ya está mapeado al número que recibe el mensaje.
2. **Conexión de Anthropic:** crearla con la API key de la cuenta que va a pagar el uso, y elegirla en "Claude responde". Verificar que el modelo figure como `claude-sonnet-5-5` en el desplegable.
3. **Pegar el prompt:** en "Claude responde" → *System Prompt*, reemplazar el texto provisorio por el contenido completo de `make/system_prompt_completo.txt`. Hasta que se pegue, el bot solo contesta que está en configuración, con el teléfono de recepción y el 107.
4. **Probar** con *Run once* desde un celular de prueba todos los casos de `prompts/casos_de_prueba.md`, y recién después activar el escenario.

**Notas**
- **Costo:** cada mensaje envía el prompt completo (unos 35.000 caracteres). Si el volumen de mensajes es alto, conviene pasar a una llamada con caché de prompt, que abarata mucho el costo.
- **Privacidad:** el historial guarda texto de las conversaciones en Make, asociado al número de WhatsApp. No se envía el número del paciente a Anthropic.

## Fuentes de la base de conocimiento

Se armó con "Resumen médicos y O.S. que atienden" (04/2026), "Arancel particular consultas médicas" (05/2026) y "Arancel particular de prestaciones diferentes" (05/2026). Se dejó afuera, a propósito, todo dato interno: CUIT, matrículas, celulares, emails, alias y cuentas bancarias, porcentajes de alquiler, por dónde se factura cada obra social y usuarios y contraseñas de portales. Tampoco se usaron el detalle de alquileres 2024 (es información financiera interna) ni los aranceles OSDE de ecografías (son valores que paga OSDE al prestador, no lo que abona el paciente).

## Puntos a confirmar

1. **Texto del mensaje fijo clínico** (ahora con el 107 SAME). Revisarlo desde el criterio médico antes de activar.
2. **Mensajes mixtos** (clínico + administrativo): el prompt manda primero el mensaje fijo completo y después responde solo la parte administrativa, sin mencionar los síntomas. Si prefieren que ante cualquier componente clínico salga *únicamente* el mensaje fijo, es un cambio de una línea.

## Datos de prueba (reemplazar antes de salir a producción)

Son inventados, solo para probar el bot. En el prompt y en la base figuran marcados como **(DATO DE PRUEBA)**, **(VALOR DE PRUEBA)**, **(DÍAS DE PRUEBA)** o **(LINK DE PRUEBA)**:
- **Centro:** nombre institucional, link de Dr. App, cómo cancelar turnos, link de Google Maps, estacionamiento, email, guardia, domingos y feriados, medios de pago y qué traer al turno.
- **Aranceles:** ecografías (Dr. Chomont), estudios audiológicos (Fga. Caeiro), electroencefalogramas infantiles (Téc. Crugnale), prácticas cardiológicas (Dr. Repezza) y medicina estética (Dra. Barnes). También el arancel diferenciado para no prestadores ($30.000) y el compensatorio del PAP con obra social ($10.000).
- **Oftalmología (Dra. Manuela Castro):** link de Treelan, coseguros y obras sociales suspendidas.
- **Días de atención** de los profesionales que no los tenían en los documentos.

## Decisiones tomadas

- Aranceles: se usan los de mayo de 2026. La columna "PAMI" es el valor que abona un afiliado PAMI.
- El bot informa el arancel diferenciado y el compensatorio.
- Para los profesionales que dan sus propios turnos, el bot no comparte su celular: deriva a recepción.
- Consulta odontológica: $50.000. La Lic. Cortinovis atiende OSDE. El Dr. Verón y la Dra. Dimilito ya no atienden en el centro.
- Datos reales del centro: Mitre 390, Los Cardales; lunes a viernes de 8 a 20 h y sábados de 8 a 13 h; recepción (0230) 4462344. Número de emergencias del mensaje fijo: 107 (SAME).
- Urgencias odontológicas: son consultas clínicas, así que el bot responde con el mensaje fijo (no se da el Instagram de la Dra. Hvala).
