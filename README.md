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
| [`make/system_prompt_completo.txt`](make/system_prompt_completo.txt) | El prompt con la base ya integrada. Es el contenido del registro `system_prompt` en Make. |
| [`make/escenario_cmc.blueprint.json`](make/escenario_cmc.blueprint.json) | Escenario de WhatsApp (producción). |
| [`make/escenario_cmc_telegram.blueprint.json`](make/escenario_cmc_telegram.blueprint.json) | Escenario de prueba por Telegram. |
| [`make/build_blueprint.py`](make/build_blueprint.py) | Regenera los tres archivos anteriores: `python3 make/build_blueprint.py`. |
| [`prompts/casos_de_prueba.md`](prompts/casos_de_prueba.md) | Casos para validar el bot antes de salir a producción (los clínicos son excluyentes). |

## Make: escenarios y recursos

Todo está en el team "My Team" de Make.

| Recurso | Para qué |
|---|---|
| Escenario **"CMCardales — Bot (prueba Telegram)"** (id 6764120) | **Activo.** Mismo bot, por un bot de Telegram de prueba (no el bot personal de Alan, que ya tiene su propio webhook). |
| Escenario **"CMCardales — Bot de WhatsApp"** (id 6763454) | **Inactivo.** Ya tiene la conexión de Anthropic; falta la de WhatsApp del número nuevo. |
| Data store **"CMCardales - Configuración del bot"** | Registro `system_prompt`: el prompt que leen los dos escenarios. Para cambiar el bot, se actualiza este registro; no hace falta tocar los escenarios. |
| Data store **"CMCardales - Historial de conversaciones"** | Historial de WhatsApp (por número). |
| Data store **"CMCardales - Historial (prueba Telegram)"** | Historial de las pruebas (por chat). |
| Conexiones **"CMCardales - Anthropic"** y **"CMC Prueba - Telegram"** | Creadas por pedido de credenciales: las claves las cargó Alan directamente en Make. |

**Cómo funciona cada mensaje**
1. **Mensaje entrante** por WhatsApp o Telegram.
2. **Router:**
   - **Texto:**
     - Lee el historial de esa persona. Si pasaron más de 24 h desde su último mensaje, arranca de cero.
     - Lee el prompt desde el data store de configuración.
     - Claude Sonnet 5.5 responde.
     - Se envía la respuesta.
     - Se guarda el historial (los últimos 3.000 caracteres).
   - **Audio, imagen u otro:** aviso de que solo lee texto, con el teléfono de recepción y el 107.
3. **Si Claude falla:** aviso con el teléfono de recepción y el 107. La ejecución termina sin error.

**Para activar WhatsApp**
1. Crear la conexión de WhatsApp Business Cloud del número nuevo de CMCardales. Elegirla en el módulo "Mensaje entrante" (crear ahí el webhook) y en los tres módulos de envío.
2. Correr los casos de `prompts/casos_de_prueba.md` (primero en Telegram) y recién después activar.

**Notas**
- **Costo:** cada mensaje envía el prompt completo (unos 35.000 caracteres). Con volumen alto conviene pasar a una llamada con caché de prompt.
- **Privacidad:** el historial guarda texto de las conversaciones en Make, asociado al número o al chat. No se envía el número del paciente a Anthropic.

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
