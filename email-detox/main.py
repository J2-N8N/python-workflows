from ipaddress import summarize_address_range
from fastapi import FastAPI
from jinja2 import pass_eval_context
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
import re

app = FastAPI(title="Email Detox")


class EmailIn(BaseModel):
    subject: str = ""
    sender: str = ""
    date: str = ""
    body_html: str | None = None
    body_text: str | None = None
    max_bullets: int = Field(default=5, ge=3, le=10)


def html_to_text(html: str) -> str:
    # Convierte html en un arbol de nodos
    soup = BeautifulSoup(html, "lxml")
    # Eliminamos etiquetas que no aportan texto util.
    for tag in soup(["script", "style", "noscript"]):
        # lo decomponemos y lo borramos del arbol para quedarno con puro texto
        tag.decompose()
    # extraemos oslo texto
    text = soup.get_text("\n")

    return text


def normalize_text(text: str) -> str:
    text = text.replace("\r", "")  # remplaza \r\n por \n. Limpia retornos de carro
    # sustituimos en caso de que tenga 3 o mas saltos de linea por 2 saldos de linea
    text = re.sub(r"\n{3,}", "\n\n", text)
    # sustituimos en caso de que tenga 2 o mas tabulaciones por un espacio en blanco
    text = re.sub(r"\t{2,}", " ", text)
    # quitamos los espacios en blanco y saltos de linea al inicio o final
    return text.strip()


def extract_links(text: str) -> list[str]:
    # buscamos urls cualquier cosa excepto: [^\s)>\]]:
    # espacios
    # )
    # >
    # ]
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    cleaned = []
    for url in urls:
        cleaned.append(url.rstrip(".,;:!?"))  # limpia puntuaciona l final del enlace
    # quitamos los duplicados
    seen = set()
    out = []
    for url in cleaned:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out[:10]


def extract_action_items(text: str) -> list[str]:
    triggers = [
        "por favor",
        "favor",
        "responde",
        "responder",
        "confirmar",
        "confirma",
        "envía",
        "enviar",
        "adjunta",
        "adjuntar",
        "pagar",
        "pago",
        "revisar",
        "revisa",
        "agendar",
        "agenda",
        "asistir",
        "asiste",
        "firma",
        "firmar",
        "aprobar",
        "aprueba",
    ]
    items = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 8:
            continue
        lower = line.lower()
        # si un trigger o termino que esta en la lista triggers esta incluido en lower (line.lower())
        if any(trigger in lower for trigger in triggers):
            if len(line) > 160:
                line = line[:157] + "..."

            items.append(line)
    # quitamos los duplicados
    seen = set()
    out = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(
                key
            )  # aqui es guardamos el item en minuscula para estandarizar. No se muestra al usuario.
            out.append(
                item
            )  # Lo guardamos con mayusculas o minusculas. Se muestra al usuario
    # regresamos 8 actions items
    return out[:8]


def guess_priority(subject: str, text: str) -> str:

    urgent_words = [
        "urgente",
        "asap",
        "hoy",
        "inmediato",
        "último aviso",
        "venc",
        "vencimiento",
    ]
    medium_words = ["mañana", "esta semana", "pendiente", "recordatorio"]
    complete_message = (subject + " " + text).lower()
    if any(key in complete_message for key in urgent_words):
        return "high"

    if any(key in complete_message for key in medium_words):
        return "medium"

    return "low"


def simple_summary(text: str, max_bullets: int) -> list[str]:
    # lista de parrafos de mas de 40 caracteres.
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 40]

    # que pasa si no tenemos partes o parrafos, evaluamos por linea
    if not parts:
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 25]
        parts = lines
    # creamos bullets
    bullets = []
    # delimitamos por max_bullets
    for part in parts[:max_bullets]:
        part = re.sub(r"\s+", " ", part)
        if len(part) > 170:
            # resumen del parrafo ... indica que hay mas texto
            part = part[:167] + "..."
        bullets.append(part)

    if not bullets:
        bullets = ["No pude generar resumen (Correo Vacio o muy corto)"]

    return bullets[:max_bullets]


@app.post("/email/detox")
def detox(payload: EmailIn):
    raw_text = payload.body_text or ""

    if payload.body_html:
        raw_text = html_to_text(payload.body_html)

    text = normalize_text(raw_text)
    links = extract_links(text)
    actions = extract_action_items(text)
    priority = guess_priority(payload.subject, text)
    summary = simple_summary(text, payload.max_bullets)
    
    return {
        "subject":payload.subject,
        "sender":payload.sender,
        "date":payload.date,
        "piority":priority,
        "summary":summary,
        "links":links,
        "chars":len(text),
        "words":len(text.split()),
        "actions_items":actions
    }
