"""Arma los blueprints de Make.com del bot de CMCardales.

Uso: python3 make/build_blueprint.py
Genera:
- make/escenario_cmc.blueprint.json: escenario de WhatsApp (producción).
- make/escenario_cmc_telegram.blueprint.json: escenario de prueba por Telegram.
- make/system_prompt_completo.txt: el system prompt con la base de conocimiento ya
  integrada. Es lo que va en el registro "system_prompt" del data store de
  configuración, que leen los dos escenarios.
Volver a correrlo cada vez que cambien el prompt o la base, y actualizar el registro.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# El modelo a veces devuelve primero un bloque de razonamiento ("thinking"):
# se toma el primer bloque de tipo texto, esté donde esté.
RESPUESTA = '{{first(map(4.content; "text"; "type"; "text"))}}'

# Recursos de Make (team "My Team")
DS_HISTORIAL_WHATSAPP = 143626  # "CMCardales - Historial de conversaciones"
DS_HISTORIAL_TELEGRAM = 182591  # "CMCardales - Historial (prueba Telegram)"
DS_CONFIGURACION = 182592  # "CMCardales - Configuración del bot", registro "system_prompt"
CONN_ANTHROPIC = 11926352  # "CMCardales - Anthropic"
CONN_TELEGRAM = 11925599  # "CMC Prueba - Telegram" (bot de prueba, no el bot personal)
HOOK_TELEGRAM = 2978501  # "CMC Prueba - Telegram Updates"
TELEGRAM_CHAT_PERMITIDO = "5383861262"  # el bot de prueba solo responde al chat de Alan

MODELO = "claude-sonnet-5-5"
MAX_HISTORIAL = 3000  # caracteres de historial que se guardan por conversación
HORAS_SESION = 24  # pasado este tiempo sin mensajes, la conversación arranca de cero
TELEFONO = "(0230) 4462344"

MENSAJE_ERROR = (
    "¡Gracias por escribirnos! En este momento no puedo responderte. "
    f"Por favor, llamá a recepción al {TELEFONO} (lunes a viernes de 8 a 20 h y sábados de 8 a 13 h).\n\n"
    "Si se trata de una urgencia, comunicate con el 107 (SAME)."
)
MENSAJE_NO_TEXTO = (
    "¡Gracias por escribirnos! Por ahora solo puedo leer mensajes de texto. ¿Me lo escribís? "
    f"También podés llamar a recepción al {TELEFONO}.\n\n"
    "Si se trata de una urgencia, comunicate con el 107 (SAME)."
)


def system_prompt():
    prompt = (RAIZ / "prompts/system_prompt.md").read_text(encoding="utf-8")
    prompt = prompt.split("\n=====\n")[1].strip()
    base = (RAIZ / "conocimiento/base_cmc.md").read_text(encoding="utf-8").strip()
    marcador = "[PEGAR ACÁ el contenido completo de conocimiento/base_cmc.md]"
    assert marcador in prompt
    return prompt.replace(marcador, base)


CANALES = {
    "whatsapp": {
        "nombre": "CMCardales — Bot de WhatsApp",
        "historial": DS_HISTORIAL_WHATSAPP,
        "trigger": {
            "module": "whatsapp-business-cloud:watchEvents2",
            "parameters": {},
            "nombre": "Mensaje entrante (número de CMCardales)",
        },
        "de": "{{1.messages[1].from}}",
        "texto": "{{1.messages[1].text.body}}",
        "es_texto": {"a": "{{1.messages[1].type}}", "o": "text:equal", "b": "text"},
        "no_es_texto": {"a": "{{1.messages[1].type}}", "o": "text:notequal", "b": "text"},
        "nombre_perfil": "{{1.contacts[1].profile.name}}",
    },
    "telegram": {
        "nombre": "CMCardales — Bot (prueba Telegram)",
        "historial": DS_HISTORIAL_TELEGRAM,
        "trigger": {
            "module": "telegram:WatchUpdates",
            "parameters": {"__IMTHOOK__": HOOK_TELEGRAM},
            "nombre": "Mensaje entrante (bot de prueba)",
        },
        "de": "{{1.message.chat.id}}",
        "texto": "{{1.message.text}}",
        "es_texto": {"a": "{{1.message.text}}", "o": "exist"},
        "no_es_texto": {"a": "{{1.message.text}}", "o": "notexist"},
        "nombre_perfil": "{{1.message.from.first_name}}",
    },
}


def enviar(canal, id_, cuerpo, nombre):
    if canal == "telegram":
        return {
            "id": id_,
            "module": "telegram:SendReplyMessage",
            "version": 1,
            "parameters": {"__IMTCONN__": CONN_TELEGRAM},
            "mapper": {"chatId": CANALES[canal]["de"], "text": cuerpo, "disableWebPagePreview": True},
            "metadata": {"designer": {"name": nombre}},
        }
    return {
        "id": id_,
        "module": "whatsapp-business-cloud:sendMessage",
        "version": 1,
        "parameters": {},
        "mapper": {
            "fromId": "{{1.metadata.phone_number_id}}",
            "to": CANALES[canal]["de"],
            "type": "text",
            "text": {"body": cuerpo, "preview_url": False},
        },
        "metadata": {"designer": {"name": nombre}},
    }


def blueprint(canal):
    c = CANALES[canal]
    hay_mensaje = {"a": c["de"], "o": "exist"}
    if canal == "telegram":
        hay_mensaje = {"a": c["de"], "o": "text:equal", "b": TELEGRAM_CHAT_PERMITIDO}
    ruta_texto = [
        {
            "id": 3,
            "module": "datastore:GetRecord",
            "version": 1,
            "parameters": {"datastore": c["historial"]},
            "mapper": {"key": c["de"], "returnWrapped": False},
            "metadata": {"designer": {"name": "Leer historial"}},
            "filter": {"name": "Mensaje de texto", "conditions": [[hay_mensaje, c["es_texto"]]]},
        },
        {
            "id": 12,
            "module": "datastore:GetRecord",
            "version": 1,
            "parameters": {"datastore": DS_CONFIGURACION},
            "mapper": {"key": "system_prompt", "returnWrapped": False},
            "metadata": {"designer": {"name": "Leer prompt del bot"}},
        },
        {
            # Si pasaron más de HORAS_SESION horas desde el último mensaje, la conversación arranca de cero
            "id": 10,
            "module": "util:ComposeTransformer",
            "version": 1,
            "parameters": {},
            "mapper": {"value": f"{{{{if(3.actualizado < addHours(now; -{HORAS_SESION}); emptystring; 3.historial)}}}}"},
            "metadata": {"designer": {"name": "Historial vigente"}},
        },
        {
            "id": 4,
            "module": "anthropic-claude:createAMessage",
            "version": 1,
            "parameters": {"__IMTCONN__": CONN_ANTHROPIC},
            "mapper": {
                "model": MODELO,
                "max_tokens": 600,
                "temperature": 0.2,
                "system": "{{12.valor}}",
                "messages": [
                    {
                        "role": "user",
                        "inputType": "single",
                        "content": f"<historial>\n{{{{10.value}}}}\n</historial>\n\n<mensaje_nuevo>\n{c['texto']}\n</mensaje_nuevo>",
                    }
                ],
            },
            "metadata": {"designer": {"name": "Claude responde"}},
            "onerror": [
                enviar(canal, 7, MENSAJE_ERROR, "Aviso si Claude falla"),
                {"id": 8, "module": "builtin:Ignore", "version": 1, "parameters": {}, "mapper": {}},
            ],
        },
        enviar(canal, 5, RESPUESTA, "Responder"),
        {
            "id": 11,
            "module": "util:ComposeTransformer",
            "version": 1,
            "parameters": {},
            "mapper": {"value": f"{{{{10.value}}}}\nPaciente: {c['texto']}\nAsistente: {RESPUESTA}"},
            "metadata": {"designer": {"name": "Historial actualizado"}},
        },
        {
            "id": 6,
            "module": "datastore:AddRecord",
            "version": 1,
            "parameters": {"datastore": c["historial"]},
            "mapper": {
                "key": c["de"],
                "overwrite": True,
                "data": {
                    # Se guardan solo los últimos MAX_HISTORIAL caracteres
                    "historial": f"{{{{substring(11.value; max(0; length(11.value) - {MAX_HISTORIAL}); length(11.value))}}}}",
                    "actualizado": "{{now}}",
                    "nombre": c["nombre_perfil"],
                },
            },
            "metadata": {"designer": {"name": "Guardar historial"}},
        },
    ]
    aviso = enviar(canal, 9, MENSAJE_NO_TEXTO, "Aviso: solo texto")
    aviso["filter"] = {"name": "Audio, imagen u otro", "conditions": [[hay_mensaje, c["no_es_texto"]]]}
    return {
        "name": c["nombre"],
        "flow": [
            {
                "id": 1,
                "module": c["trigger"]["module"],
                "version": 1,
                "parameters": c["trigger"]["parameters"],
                "mapper": {},
                "metadata": {"designer": {"name": c["trigger"]["nombre"]}},
            },
            {
                "id": 2,
                "module": "builtin:BasicRouter",
                "version": 1,
                "mapper": None,
                "routes": [{"flow": ruta_texto}, {"flow": [aviso]}],
            },
        ],
        "metadata": {"version": 1, "scenario": {"roundtrips": 1, "maxErrors": 3, "autoCommit": True, "sequential": True}},
    }


if __name__ == "__main__":
    (RAIZ / "make/system_prompt_completo.txt").write_text(system_prompt() + "\n", encoding="utf-8")
    for canal, archivo in [("whatsapp", "escenario_cmc"), ("telegram", "escenario_cmc_telegram")]:
        salida = RAIZ / f"make/{archivo}.blueprint.json"
        salida.write_text(json.dumps(blueprint(canal), ensure_ascii=False, indent=1), encoding="utf-8")
        print("Blueprint generado:", salida)
