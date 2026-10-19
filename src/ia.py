"""Entrada en lenguaje natural con un LLM (Google Gemini) → campos del formulario.

Reglas del proyecto: la IA solo convierte el texto en los campos de entrada; el usuario los ve y
los corrige; la IA nunca puntúa ni recomienda. La salida está restringida por un esquema JSON
(ocupación y municipio solo pueden ser valores de nuestras listas) y se valida aquí. Si no hay
clave, o ningún modelo responde a tiempo, se usa el analizador determinista de `src/texto.py`.

Clave: variable `GOOGLE_AI` (o `GEMINI_API_KEY`) en el entorno, en `.env` (no se sube a git) o
en `.streamlit/secrets.toml`.
"""
import json
import os
import time
from dataclasses import dataclass, field

import requests

from .config import ROOT
from .texto import _municipio, _norm, interpretar as interpretar_reglas

# Del más rápido al más capaz; si uno falla (cuota agotada, caído, retirado) se prueba el siguiente
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
TIMEOUT_S = 12
CAMPOS = ("ocupacion", "ine", "coche", "hijo", "formacion", "T", "cp")


def clave() -> str | None:
    for nombre in ("GOOGLE_AI", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        if os.environ.get(nombre):
            return os.environ[nombre].strip()
    env = ROOT / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            k, _, v = linea.partition("=")
            if k.strip() in ("GOOGLE_AI", "GEMINI_API_KEY", "GOOGLE_API_KEY") and v.strip():
                return v.strip().strip("\"'")
    try:
        import streamlit as st
        for nombre in ("GOOGLE_AI", "GEMINI_API_KEY"):
            if nombre in st.secrets:
                return str(st.secrets[nombre])
    except Exception:
        pass
    return None


@dataclass
class Interpretacion:
    campos: dict                       # ocupacion, ine, coche, hijo, formacion, T (None = no lo dijo)
    metodo: str                        # "ia" o "reglas"
    modelo: str | None = None
    ocupacion_dicha: str | None = None  # cómo la describió la persona
    ocupacion_aproximada: bool = False  # la suya no está en la lista: se eligió la más parecida
    aviso: str | None = None           # por qué se usó el respaldo, si fue el caso
    segundos: float = 0.0
    intentos: list = field(default_factory=list)


def _instrucciones(ocupaciones: dict[str, str]) -> str:
    lista = "\n".join(f"- {i}: {n}" for i, n in ocupaciones.items())
    return f"""Eres el asistente de entrada de Alcanza, una herramienta pública de orientación laboral de la
Comunidad de Madrid. Lee lo que cuenta una persona que busca empleo y rellena SOLO estos campos.
No des consejos ni valoraciones. Si un dato no aparece, déjalo en null; no lo inventes.

- ocupacion_id: la ocupación en la que ha trabajado o quiere trabajar, elegida de esta lista:
{lista}
  Si dice una ocupación que no está, elige la más parecida por tareas y competencias y marca
  ocupacion_aproximada = true. Si no menciona ninguna, null.
- ocupacion_dicha: la ocupación con sus propias palabras (null si no la dice).
- municipio: municipio de la Comunidad de Madrid donde VIVE (no donde trabajaba antes), con el
  nombre exacto de la lista permitida. Interpreta abreviaturas y nombres populares («Sanse» =
  San Sebastián de los Reyes, «Alcalá» = Alcalá de Henares, «Rivas» = Rivas-Vaciamadrid).
  Un barrio o distrito de Madrid es «Madrid».
- coche: true si dispone de coche, moto u otro vehículo propio para ir a trabajar; false si
  dice que no tiene, que no conduce o que no tiene carné.
- hijo_0_3: true si tiene a su cargo algún hijo o hija de 0 a 3 años (bebé, guardería, «un niño
  de 2 años»); false si menciona hijos pero todos mayores de 3 años; null si no habla de hijos.
- formacion: true si está dispuesta a estudiar o formarse; false si dice que no; null si no lo dice.
- tiempo_max_min: tiempo máximo de viaje de ida en minutos («media hora» = 30, «tres cuartos de
  hora» = 45, «hora y media» = 90). null si no lo dice."""


def _esquema(ocupaciones: dict[str, str], municipios: list[str]) -> dict:
    return {"type": "object", "properties": {
        "ocupacion_id": {"type": "string", "enum": list(ocupaciones), "nullable": True},
        "ocupacion_dicha": {"type": "string", "nullable": True},
        "ocupacion_aproximada": {"type": "boolean"},
        "municipio": {"type": "string", "enum": municipios, "nullable": True},
        "coche": {"type": "boolean", "nullable": True},
        "hijo_0_3": {"type": "boolean", "nullable": True},
        "formacion": {"type": "boolean", "nullable": True},
        "tiempo_max_min": {"type": "integer", "nullable": True},
    }, "required": ["ocupacion_id", "ocupacion_dicha", "ocupacion_aproximada", "municipio", "coche", "hijo_0_3",
                    "formacion", "tiempo_max_min"]}


def _llamar(modelo: str, k: str, texto: str, sistema: str, esquema: dict) -> dict:
    cuerpo = {"systemInstruction": {"parts": [{"text": sistema}]},
              "contents": [{"role": "user", "parts": [{"text": texto[:2000]}]}],
              "generationConfig": {"responseMimeType": "application/json", "responseSchema": esquema,
                                   "temperature": 0, "maxOutputTokens": 400}}
    r = requests.post(URL.format(modelo), headers={"x-goog-api-key": k}, json=cuerpo, timeout=TIMEOUT_S)
    if not r.ok:
        msg = (r.json().get("error", {}).get("message", "") if r.headers.get("content-type", "").startswith(
            "application/json") else r.text)[:120]
        raise RuntimeError(f"HTTP {r.status_code}: {msg}")
    partes = r.json()["candidates"][0]["content"]["parts"]
    return json.loads("".join(p.get("text", "") for p in partes))


def _validar(r: dict, ocupaciones: dict[str, str], municipios: dict[str, str]) -> dict:
    """Solo pasan valores de nuestras listas y tipos correctos; lo demás queda en None."""
    por_nombre = {_norm(n): ine for ine, n in municipios.items()}
    m = r.get("municipio")
    ine = por_nombre.get(_norm(m)) if isinstance(m, str) else None
    if isinstance(m, str) and ine is None:
        ine = _municipio(" " + _norm(m) + " ", municipios)
    T = r.get("tiempo_max_min")
    booleano = lambda x: x if isinstance(x, bool) else None
    return {"ocupacion": r.get("ocupacion_id") if r.get("ocupacion_id") in ocupaciones else None,
            "ine": ine,
            "coche": booleano(r.get("coche")),
            "hijo": booleano(r.get("hijo_0_3")),
            "formacion": booleano(r.get("formacion")),
            "T": int(T) if isinstance(T, (int, float)) and 5 <= T <= 240 else None,
            "cp": None}  # el código postal (barrio de Madrid) lo ponen siempre las reglas


def interpretar(texto: str, ocupaciones: dict[str, str], municipios: dict[str, str],
                usar_ia: bool = True, modelos: list[str] | None = None) -> Interpretacion:
    """ocupaciones: {id: nombre}; municipios: {ine: nombre oficial}."""
    reglas = interpretar_reglas(texto, municipios)
    k = clave() if usar_ia else None
    if not k:
        return Interpretacion(reglas, "reglas", aviso=None if not usar_ia else "sin clave de IA configurada")
    sistema = _instrucciones(ocupaciones)
    esquema = _esquema(ocupaciones, sorted(municipios.values()))
    t0, intentos = time.time(), []
    for modelo in modelos or MODELOS:
        try:
            r = _llamar(modelo, k, texto, sistema, esquema)
            campos = _validar(r, ocupaciones, municipios)
            # lo que la IA no ha rellenado se completa con las reglas (nunca al revés)
            for c in CAMPOS:
                if campos[c] is None and reglas[c] is not None:
                    campos[c] = reglas[c]
            return Interpretacion(campos, "ia", modelo, r.get("ocupacion_dicha"),
                                  bool(r.get("ocupacion_aproximada")) and campos["ocupacion"] is not None,
                                  segundos=round(time.time() - t0, 1), intentos=intentos)
        except Exception as e:  # cuota agotada, modelo retirado, red, JSON inválido…
            intentos.append(f"{modelo}: {str(e)[:100]}")
    return Interpretacion(reglas, "reglas", aviso="la IA no respondió; se han usado las reglas",
                          segundos=round(time.time() - t0, 1), intentos=intentos)
