"""Arma el blueprint del escenario de Make.com del bot de WhatsApp de CMCardales.

Uso: python3 make/build_blueprint.py
Genera:
- make/escenario_cmc.blueprint.json: el escenario (importable en Make).
- make/system_prompt_completo.txt: el system prompt con la base de conocimiento ya
  integrada, para pegar en el módulo "Claude responde".
Volver a correrlo cada vez que cambien el prompt o la base.
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA_STORE_ID = 143626  # "CMCardales - Historial de conversaciones"
MODELO = "claude-sonnet-5-5"
MAX_HISTORIAL = 3000  # caracteres de historial que se guardan por conversación
HORAS_SESION = 24  # pasado este tiempo sin mensajes, la conversación arranca de cero
TELEFONO = "(0230) 4462344"


def system_prompt():
    prompt = (RAIZ / "prompts/system_prompt.md").read_text(encoding="utf-8")
    prompt = prompt.split("\n=====\n")[1].strip()
    base = (RAIZ / "conocimiento/base_cmc.md").read_text(encoding="utf-8").strip()
    marcador = "[PEGAR ACÁ el contenido completo de conocimiento/base_cmc.md]"
    assert marcador in prompt
    return prompt.replace(marcador, base)


# Referencias a datos de módulos anteriores (sintaxis de mapeo de Make)
DE = "{{1.messages[1].from}}"
TEXTO = "{{1.messages[1].text.body}}"
PHONE_ID = "{{1.metadata.phone_number_id}}"
RESPUESTA = "{{4.content[1].text}}"

# El prompt completo (~35.000 caracteres) se pega a mano en el módulo de Claude desde
# make/system_prompt_completo.txt. Hasta entonces, este texto mínimo mantiene el bot seguro.
SYSTEM_PROVISORIO = (
    "El asistente de CMCardales está en configuración. Ante cualquier mensaje, respondé únicamente, "
    "textual: \"¡Gracias por escribirnos! Nuestro asistente virtual está en configuración. "
    f"Por favor, llamá a recepción al {TELEFONO}. Si se trata de una urgencia, comunicate con el 107 (SAME).\""
)

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


def enviar(id_, cuerpo, nombre):
    return {
        "id": id_,
        "module": "whatsapp-business-cloud:sendMessage",
        "version": 1,
        "parameters": {},
        "mapper": {
            "fromId": PHONE_ID,
            "to": DE,
            "type": "text",
            "text": {"body": cuerpo, "preview_url": False},
        },
        "metadata": {"designer": {"name": nombre}},
    }


def hay_mensaje():
    return {"a": "{{1.messages[1].from}}", "o": "exist"}


def blueprint():
    ruta_texto = [
        {
            "id": 3,
            "module": "datastore:GetRecord",
            "version": 1,
            "parameters": {"datastore": DATA_STORE_ID},
            "mapper": {"key": DE},
            "metadata": {"designer": {"name": "Leer historial"}},
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
            "parameters": {},
            "mapper": {
                "model": MODELO,
                "max_tokens": 600,
                "temperature": 0.2,
                "system": SYSTEM_PROVISORIO,
                "messages": [
                    {
                        "role": "user",
                        "inputType": "single",
                        "content": f"<historial>\n{{{{10.value}}}}\n</historial>\n\n<mensaje_nuevo>\n{TEXTO}\n</mensaje_nuevo>",
                    }
                ],
            },
            "metadata": {"designer": {"name": "Claude responde"}},
            "onerror": [
                enviar(7, MENSAJE_ERROR, "Aviso si Claude falla"),
                {"id": 8, "module": "builtin:Ignore", "version": 1, "parameters": {}, "mapper": {}},
            ],
        },
        enviar(5, RESPUESTA, "Responder por WhatsApp"),
        {
            "id": 11,
            "module": "util:ComposeTransformer",
            "version": 1,
            "parameters": {},
            "mapper": {"value": f"{{{{10.value}}}}\nPaciente: {TEXTO}\nAsistente: {RESPUESTA}"},
            "metadata": {"designer": {"name": "Historial actualizado"}},
        },
        {
            "id": 6,
            "module": "datastore:AddRecord",
            "version": 1,
            "parameters": {"datastore": DATA_STORE_ID},
            "mapper": {
                "key": DE,
                "overwrite": True,
                "data": {
                    # Se guardan solo los últimos MAX_HISTORIAL caracteres
                    "historial": f"{{{{substring(11.value; max(0; length(11.value) - {MAX_HISTORIAL}); length(11.value))}}}}",
                    "actualizado": "{{now}}",
                    "nombre": "{{1.contacts[1].profile.name}}",
                },
            },
            "metadata": {"designer": {"name": "Guardar historial"}},
        },
    ]
    ruta_no_texto = [enviar(9, MENSAJE_NO_TEXTO, "Aviso: solo texto")]
    return {
        "name": "CMCardales — Bot de WhatsApp",
        "flow": [
            {
                "id": 1,
                "module": "whatsapp-business-cloud:watchEvents2",
                "version": 1,
                "parameters": {},
                "mapper": {},
                "metadata": {"designer": {"name": "Mensaje entrante (número de CMCardales)"}},
            },
            {
                "id": 2,
                "module": "builtin:BasicRouter",
                "version": 1,
                "mapper": None,
                "routes": [
                    {
                        "flow": [dict(ruta_texto[0], filter={
                            "name": "Mensaje de texto",
                            "conditions": [[hay_mensaje(), {"a": "{{1.messages[1].type}}", "o": "text:equal", "b": "text"}]],
                        })] + ruta_texto[1:]
                    },
                    {
                        "flow": [dict(ruta_no_texto[0], filter={
                            "name": "Audio, imagen u otro",
                            "conditions": [[hay_mensaje(), {"a": "{{1.messages[1].type}}", "o": "text:notequal", "b": "text"}]],
                        })]
                    },
                ],
            },
        ],
        "metadata": {"version": 1, "scenario": {"roundtrips": 1, "maxErrors": 3, "autoCommit": True, "sequential": True}},
    }


if __name__ == "__main__":
    (RAIZ / "make/system_prompt_completo.txt").write_text(system_prompt() + "\n", encoding="utf-8")
    salida = RAIZ / "make/escenario_cmc.blueprint.json"
    salida.write_text(json.dumps(blueprint(), ensure_ascii=False, indent=1), encoding="utf-8")
    print("Blueprint generado:", salida)
