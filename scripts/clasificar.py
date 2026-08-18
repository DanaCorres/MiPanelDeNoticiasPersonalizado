"""Clasificación de titulares por tema.

Dos trabajos:
  1. Repartir los titulares mexicanos que vienen de portadas generales entre
     Política, Economía, CDMX, Opinión y Tecnología.
  2. Decidir si un titular de las fuentes de tecnología habla de IA.

Todo se hace con listas de palabras clave que puedes editar a mano. No hay
modelo ni API de por medio: es texto contra texto, así que el panel funciona
aunque te quedes sin conexión a cualquier servicio externo.
"""

from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------
# Utilidades de texto
# --------------------------------------------------------------------------


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos y sin espacios de más."""
    texto = unicodedata.normalize("NFD", texto or "")
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto.lower()).strip()


def _compilar(palabras: list[str]) -> list[re.Pattern]:
    """Convierte cada palabra clave en una expresión con límites de palabra.

    El sufijo opcional `(?:e?s)?` hace que "modelo de lenguaje" también
    encuentre "modelos de lenguaje" sin que tengas que escribir el plural.
    """
    patrones = []
    for palabra in palabras:
        piezas = [re.escape(p) + r"(?:e?s)?" for p in normalizar(palabra).split(" ")]
        patrones.append(re.compile(r"(?<!\w)" + r"\s+".join(piezas) + r"(?!\w)"))
    return patrones


# --------------------------------------------------------------------------
# Palabras clave por subsección nacional
# --------------------------------------------------------------------------
# El orden importa: si un titular empata, gana la subsección que aparece
# primero en PRIORIDAD (más abajo).

CLAVES_NACIONAL: dict[str, list[str]] = {
    "cdmx": [
        "cdmx", "ciudad de mexico", "capitalina", "capitalino", "clara brugada",
        "jefatura de gobierno", "gobierno capitalino", "congreso capitalino",
        "alcaldia", "alcaldias", "iztapalapa", "coyoacan", "tlalpan", "azcapotzalco",
        "xochimilco", "milpa alta", "cuauhtemoc", "miguel hidalgo", "venustiano carranza",
        "gustavo a. madero", "benito juarez", "alvaro obregon", "magdalena contreras",
        "cuajimalpa", "iztacalco", "tlahuac", "metro de la ciudad", "metrobus",
        "cablebus", "ecobici", "paseo de la reforma", "zocalo", "valle de mexico", "aicm",
        "linea 12", "linea 1 del metro", "sistema de aguas", "chapultepec",
    ],
    "economia": [
        "economia", "economico", "inflacion", "banxico", "banco de mexico", "peso mexicano",
        "tipo de cambio", "bolsa mexicana", "bmv", "pib", "recesion", "aranceles",
        "t-mec", "tratado comercial", "exportaciones", "importaciones", "remesas",
        "inversion", "inversionistas", "empleo", "desempleo", "salario minimo",
        "sat", "impuestos", "hacienda", "presupuesto", "deuda publica", "pemex",
        "cfe", "calificadora", "moody's", "fitch", "fmi", "banco mundial",
        "canasta basica", "gasolina", "combustibles", "mercados", "wall street",
        "nearshoring", "infonavit", "afore", "credito",
    ],
    "tecnologia": [
        "tecnologia", "tecnologica", "inteligencia artificial", "ia generativa",
        "openai", "chatgpt", "anthropic", "claude", "google", "gemini", "microsoft",
        "apple", "meta", "nvidia", "semiconductores", "chips", "software", "app",
        "aplicacion movil", "ciberseguridad", "hackeo", "ciberataque", "datos personales",
        "telecomunicaciones", "internet", "banda ancha", "5g", "starlink",
        "redes sociales", "tiktok", "whatsapp", "criptomonedas", "bitcoin",
        "startup", "streaming", "videojuegos", "robot", "algoritmo",
    ],
    "opinion": [
        "columna", "editorial", "opinion", "analisis", "tribuna", "punto de vista",
    ],
    "politica": [
        "politica", "presidencia", "presidenta", "sheinbaum", "palacio nacional",
        "mananera", "gobierno federal", "morena", "pan", "pri", "prd",
        "movimiento ciudadano", "pt", "pvem", "senado", "senadores", "diputados",
        "camara baja", "camara alta", "congreso de la union", "reforma judicial",
        "suprema corte", "scjn", "ine", "tepjf", "elecciones", "gobernador",
        "gobernadora", "fiscalia", "fgr", "sedena", "marina", "guardia nacional",
        "seguridad publica", "narcotrafico", "crimen organizado", "cartel",
        "extradicion", "derechos humanos", "migracion", "migrantes", "aduanas",
        "corrupcion", "secretaria de gobernacion", "segob", "sre", "canciller",
        "ssa", "salud publica", "imss", "issste", "consulta popular", "amlo",
    ],
}

PRIORIDAD = ["cdmx", "opinion", "economia", "tecnologia", "politica"]

_CLAVES_COMPILADAS = {k: _compilar(v) for k, v in CLAVES_NACIONAL.items()}

# Pistas que vienen en la URL del artículo (los medios suelen delatarse solos)
PISTAS_URL = {
    "politica": ["/politica", "/nacional", "/seguridad", "/mexico/politica"],
    "economia": ["/economia", "/dinero", "/mercados", "/negocios", "/empresas", "/finanzas"],
    "cdmx": ["/cdmx", "/ciudad-de-mexico", "/capital", "/comunidad"],
    "opinion": ["/opinion", "/columna", "/editorial", "/blogs", "/firmas"],
    "tecnologia": ["/tecnologia", "/tech", "/ciencia-y-tecnologia", "/gadgets"],
}


def clasificar_nacional(titulo: str, resumen: str, url: str) -> str | None:
    """Devuelve la subsección nacional del titular, o None si no encaja en ninguna."""
    url_baja = (url or "").lower()
    for subseccion in PRIORIDAD:
        for pista in PISTAS_URL.get(subseccion, []):
            if pista in url_baja:
                return subseccion

    texto = normalizar(f"{titulo} {resumen}")
    puntajes: dict[str, int] = {}
    for subseccion, patrones in _CLAVES_COMPILADAS.items():
        puntaje = sum(1 for patron in patrones if patron.search(texto))
        if puntaje:
            puntajes[subseccion] = puntaje

    if not puntajes:
        return None

    maximo = max(puntajes.values())
    empatados = [s for s, p in puntajes.items() if p == maximo]
    for subseccion in PRIORIDAD:
        if subseccion in empatados:
            return subseccion
    return empatados[0]


# --------------------------------------------------------------------------
# Detección de temas de inteligencia artificial
# --------------------------------------------------------------------------

CLAVES_IA = [
    "inteligencia artificial", "artificial intelligence", "ia generativa",
    "generative ai", "machine learning", "aprendizaje automatico", "deep learning",
    "red neuronal", "neural network", "modelo de lenguaje", "language model",
    "llm", "chatbot", "openai", "chatgpt", "sora", "anthropic", "claude",
    "deepmind", "gemini", "copilot", "midjourney", "stable diffusion",
    "hugging face", "mistral", "deepseek", "perplexity", "nvidia", "agi",
    "superinteligencia", "superintelligence", "algoritmo", "algorithm",
    "centro de datos", "data center", "semiconductores", "chips de ia",
    "ai chips", "robotica", "robotics", "agente de ia", "ai agent", "alucinacion",
    "regulacion de la ia", "ai act", "derechos de autor e ia",
]

_CLAVES_IA_COMPILADAS = _compilar(CLAVES_IA)
_SIGLA_IA = re.compile(r"(?<!\w)(A\.?I\.?|IA)(?!\w)")


def es_de_ia(titulo: str, resumen: str, url: str) -> bool:
    """True si el titular habla de inteligencia artificial."""
    url_baja = (url or "").lower()
    if any(p in url_baja for p in ("artificial-intelligence", "/ai/", "-ai-", "inteligencia-artificial")):
        return True

    texto = normalizar(f"{titulo} {resumen}")
    if any(patron.search(texto) for patron in _CLAVES_IA_COMPILADAS):
        return True

    # "AI" e "IA" como siglas: se revisan sobre el texto original, con mayúsculas,
    # para no confundirlas con palabras sueltas.
    return bool(_SIGLA_IA.search(f"{titulo} {resumen}"))
