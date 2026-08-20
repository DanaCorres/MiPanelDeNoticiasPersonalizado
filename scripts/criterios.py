"""Reglas editoriales del panel (ver criterios.md).

Tres trabajos, todos sin API ni modelo de por medio:

  1. País por contenido: una nota va a la sección del país del que trata, no
     del feed por el que llegó.  (Regla 1)
  2. Ruido de trámites: los instructivos de servicio no entran.  (Regla 2)
  3. Tope por fuente: ningún medio acapara una sección.  (Regla 4)

Todo es texto contra texto, así que el panel sigue funcionando sin conexión a
ningún servicio externo.
"""

from __future__ import annotations

import re

from clasificar import _compilar, normalizar

# --------------------------------------------------------------------------
# Regla 1 — El país lo decide el contenido, no la fuente
# --------------------------------------------------------------------------
# Infobae, Aristegui y Milenio publican cobertura internacional que hoy cae
# por default en Nacional. Estas listas la mandan a donde corresponde.

PAISES: dict[str, list[str]] = {
    "colombia": [
        "colombia", "colombiano", "colombiana", "bogota", "medellin", "cali",
        "barranquilla", "cartagena", "petro", "gustavo petro", "casa de narino",
        "farc", "eln", "clan del golfo", "uribe", "duque", "santos",
        "de la espriella", "cambio radical", "pacto historico", "fiscalia colombiana",
    ],
    "argentina": [
        "argentina", "argentino", "buenos aires", "casa rosada", "milei",
        "javier milei", "kirchner", "cristina fernandez", "peronismo", "peronista",
        "massa", "macri", "bullrich", "villarruel", "cordoba argentina",
        "rosario", "la plata", "banco central de la republica argentina",
    ],
    "espana": [
        "espana", "espanol", "espanola", "madrid", "barcelona", "cataluna",
        "andalucia", "valencia", "sevilla", "moncloa", "pedro sanchez",
        "feijoo", "abascal", "psoe", "partido popular", "vox", "podemos",
        "sumar", "cortes generales", "congreso de los diputados espanol",
        "casa real", "felipe vi",
    ],
}

# Cualquier otro país: la nota se va a la sección internacional.
EXTRANJERO = [
    "nicaragua", "nicaraguense", "ortega", "venezuela", "venezolano", "maduro",
    "caracas", "cuba", "cubano", "la habana", "diaz-canel", "chile", "chileno",
    "boric", "peru", "peruano", "lima", "bolivia", "boliviano", "ecuador",
    "ecuatoriano", "noboa", "guatemala", "honduras", "el salvador", "bukele",
    "costa rica", "panama", "republica dominicana", "haiti", "uruguay",
    "paraguay", "brasil", "brasileno", "lula", "bolsonaro", "estados unidos",
    "washington", "casa blanca", "trump", "biden", "pentagono", "canada",
    "francia", "alemania", "reino unido", "italia", "rusia", "putin", "ucrania",
    "zelenski", "china", "xi jinping", "japon", "corea del norte", "corea del sur",
    "india", "israel", "gaza", "palestina", "netanyahu", "iran", "egipto",
    "arabia saudita", "turquia", "sudafrica", "nigeria", "union europea",
    "onu", "otan", "amnistia internacional", "human rights watch",
]

# Marcas de que la nota sí es de México. Si aparecen junto a un país
# extranjero, es una nota bilateral y se queda en Nacional (el caso Harfuch
# con la ministra argentina de Seguridad).
MEXICO = [
    "mexico", "mexicano", "mexicana", "sheinbaum", "claudia sheinbaum", "amlo",
    "lopez obrador", "palacio nacional", "mananera", "morena", "cdmx",
    "ciudad de mexico", "gobierno federal", "sre", "segob", "sedena", "semar",
    "guardia nacional", "fgr", "scjn", "ine", "tepjf", "senado de la republica",
    "camara de diputados", "banxico", "pemex", "cfe", "imss", "issste", "sat",
    "harfuch", "garcia harfuch", "ebrard", "de la fuente", "gertz manero",
    "peso mexicano", "t-mec", "jalisco", "nuevo leon", "monterrey", "guadalajara",
    "sinaloa", "michoacan", "oaxaca", "chiapas", "veracruz", "puebla",
    "baja california", "sonora", "chihuahua", "tamaulipas", "guanajuato",
    "queretaro", "yucatan", "quintana roo", "cancun", "tijuana",
]

_PAISES_COMPILADOS = {k: _compilar(v) for k, v in PAISES.items()}
_EXTRANJERO_COMPILADO = _compilar(EXTRANJERO)
_MEXICO_COMPILADO = _compilar(MEXICO)


def _cuenta(patrones, texto: str) -> int:
    return sum(1 for p in patrones if p.search(texto))


def reasignar_pais(titulo: str, resumen: str, seccion: str) -> str:
    """Devuelve la sección correcta de una nota que llegó a 'nacional'.

    Solo actúa sobre notas mexicanas: las demás secciones ya vienen del feed
    correcto. Si la nota menciona México y otro país a la vez, es bilateral y
    se queda donde está.
    """
    if seccion != "nacional":
        return seccion

    texto = normalizar(f"{titulo} {resumen}")

    if _cuenta(_MEXICO_COMPILADO, texto):
        return "nacional"  # bilateral o mexicana: se queda

    for destino, patrones in _PAISES_COMPILADOS.items():
        if _cuenta(patrones, texto):
            return destino

    if _cuenta(_EXTRANJERO_COMPILADO, texto):
        return "internacional"

    return "nacional"


# --------------------------------------------------------------------------
# Regla 2 — Ruido de trámites y servicio
# --------------------------------------------------------------------------

# El patrón: titular en forma de pregunta de requisitos, cuerpo dirigido al
# lector. La prueba de fondo es si la nota seguiría vigente en seis meses.
TRAMITE = [
    r"\bquienes pueden\b",
    r"\bcomo (tramitar|registrar|solicitar|obtener|descargar|consultar|sacar|darse de alta)\b",
    r"\bcomo (te )?registr",
    r"\brequisitos?\s+(para|de|que)\b",
    r"\bpaso a paso\b",
    r"\bque (documentos|papeles) (se )?(necesit|requier|pid)",
    r"\bcuando (cae|se paga|depositan|pagan)\b",
    r"\bfechas? de pago\b",
    r"\bcalendario (escolar|de pagos)\b",
    r"\bguia (completa|paso a paso)\b",
    r"\btodo lo que (debes|tienes que) saber\b",
    r"\bcuanto (cuesta|dura) el tramite\b",
]

# Vetos: si aparece alguno de estos, la nota NO es trámite aunque hable de
# trámites. Un lanzamiento es noticia.
LANZAMIENTO = [
    r"\b(lanza|lanzo|lanzara|estrena|estreno|presenta|presento|anuncia|anuncio)\b",
    r"\b(aprueba|aprobo|autoriza|autorizo|publica|publico) (en el dof|el decreto|la reforma)\b",
    r"\b(amplia|amplio|extiende|extendio|incorpora|incorporo|suma|sumo)\b",
    r"\b(entra|entro) en vigor\b",
    r"\b(arranca|arranco|inicia|inicio|comienza|comenzo) (el|la|con)\b",
    r"\bnuevo (programa|sistema|portal|tramite|apoyo|beneficio)\b",
    r"\bnueva (plataforma|modalidad|regla|prestacion|pension)\b",
    r"\bpor primera vez\b",
    r"\bdiario oficial\b",
    r"\bdof\b",
    # Alguien DECIDE los requisitos: es una decisión, no un instructivo.
    r"\b(define|definio|establece|establecio|fija|fijo|modifica|modifico|"
    r"endurece|endurecio|flexibiliza|flexibilizo|elimina|elimino)\b",
]

# Excepción crítica: digitalizar trámites es literalmente el trabajo de la
# ATDT, así que sus notas hablan de trámites todo el tiempo. Ante la duda,
# conservar. (Regla 7 de criterios.md)
ATDT = [
    r"\batdt\b",
    r"\bagencia de transformacion digital\b",
    r"\bpena merino\b",
    r"\bllave mx\b",
    r"\bidentidad digital\b",
    r"\bexpediente unico\b",
    r"\binteroperabilidad\b",
    r"\bautonomia tecnologica\b",
    r"\bgobierno digital\b",
]

_TRAMITE = [re.compile(p) for p in TRAMITE]
_LANZAMIENTO = [re.compile(p) for p in LANZAMIENTO]
_ATDT = [re.compile(p) for p in ATDT]


def es_atdt(titulo: str, resumen: str) -> bool:
    """True si la nota habla de la Agencia de Transformación Digital."""
    texto = normalizar(f"{titulo} {resumen}")
    return any(p.search(texto) for p in _ATDT)


def es_tramite(titulo: str, resumen: str) -> bool:
    """True si la nota es un instructivo de servicio y no debe entrar.

    Se evalúa SOLO el titular. Antes se leía también el resumen y eso barría
    notas legítimas: basta que el cuerpo mencione "requisitos" de pasada para
    que una nota de política se fuera al descarte.
    """
    texto = normalizar(titulo)

    if any(p.search(texto) for p in _ATDT):
        return False
    if any(p.search(texto) for p in _LANZAMIENTO):
        return False
    return any(p.search(texto) for p in _TRAMITE)


# --------------------------------------------------------------------------
# Regla 4 — Tope por fuente
# --------------------------------------------------------------------------


def aplicar_tope(articulos: list[dict], tope: int) -> list[dict]:
    """Reordena para que ninguna fuente acapare el principio de la sección.

    No borra nada: las notas que rebasan el tope de su medio se marcan como
    desplazadas y bajan al final. Es un cambio de orden, no un filtro — el
    ruido de la regla 2 ya se descartó antes de llegar aquí.
    """
    if tope <= 0:
        return articulos

    conteo: dict[str, int] = {}
    principales: list[dict] = []
    desplazadas: list[dict] = []

    for nota in articulos:
        medio = nota.get("fuente", "")
        conteo[medio] = conteo.get(medio, 0) + 1
        if conteo[medio] <= tope:
            nota["desplazada"] = False
            principales.append(nota)
        else:
            nota["desplazada"] = True
            desplazadas.append(nota)

    return principales + desplazadas
