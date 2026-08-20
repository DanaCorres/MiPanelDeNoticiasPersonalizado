"""Capa de curaduría con la API de Claude (paso 4 del pipeline).

Qué hace, en una sola pasada por lote:
  - decide sección y subsección leyendo el titular, no la etiqueta del feed;
  - asigna prioridad de 1 a 5 según criterios.md;
  - marca las que son ruido de servicio;
  - agrupa las coberturas del mismo hecho;
  - escribe resumen solo si `resumenes_ia: true` en fuentes.yaml (apagado por
    defecto, porque es con mucho lo más caro de pedirle al modelo).

Tres cosas cuidan el costo:
  1. Los veredictos del día se guardan en docs/datos/veredictos.json, así que
     cada corrida solo paga por las notas nuevas, no por las de la mañana.
  2. Los criterios editoriales viajan con caché de prompt: se cobran completos
     una vez y al 10% en las llamadas siguientes.
  3. Al final se imprime el costo estimado de la corrida.

Todo es opcional. Si no hay ANTHROPIC_API_KEY, si la API falla o si algo
viene mal formado, el recolector sigue con la clasificación por palabras
clave y el panel se publica igual. Nunca tumba la corrida.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

API = "https://api.anthropic.com/v1/messages"
RAIZ = Path(__file__).resolve().parents[1]
CRITERIOS = RAIZ / "criterios.md"
CACHE = RAIZ / "docs" / "datos" / "veredictos.json"
CDMX = ZoneInfo("America/Mexico_City")

# Dólares por millón de tokens. Si cambian los precios, se corrigen aquí; solo
# se usan para estimar el costo que se imprime en el log.
PRECIOS = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0),
}

INSTRUCCIONES = """\
Eres el editor de un panel personal de monitoreo de noticias. Tu trabajo es \
clasificar y jerarquizar titulares siguiendo los criterios editoriales que se \
te dan abajo. Esos criterios mandan sobre cualquier intuición general tuya \
sobre qué es importante.

Para CADA nota que recibas devuelve un objeto con:
  "id"         : el id tal cual llegó, sin modificar
  "seccion"    : una de {secciones}
  "subseccion" : si seccion es "nacional", una de {subsecciones}; si no, null
  "prioridad"  : entero 1-5. 5 = va hasta arriba, 1 = apenas merece estar
  "ruido"      : true si es contenido de servicio/trámite/SEO que no debe entrar
{bloque_resumen}  "historia"   : identificador corto en minúsculas y con guiones del hecho que \
narra la nota (ej. "renuncia-monica-soto-tepjf"). Dos notas del mismo hecho, \
aunque sean de medios distintos y con titulares distintos, deben compartir el \
mismo valor. Sirve para agrupar coberturas.

Responde ÚNICAMENTE con un arreglo JSON. Sin preámbulo, sin explicación, sin \
bloques de código. Un objeto por cada nota recibida, en el mismo orden.

--- CRITERIOS EDITORIALES ---
{criterios}
"""

BLOQUE_RESUMEN = """\
  "resumen"    : dos líneas en español (máximo 40 palabras) con qué pasó, quién \
lo decidió y a quién afecta. Si la nota ya trae resumen propio, devuelve null. \
No interpretes, no adjetives, no completes lo que el titular no dice. Si el \
titular no alcanza para un resumen honesto, devuelve null.
"""


def _hoy() -> str:
    return datetime.now(CDMX).strftime("%Y-%m-%d")


def leer_cache() -> dict[str, dict]:
    """Veredictos ya emitidos hoy. Se vacía solo al cambiar el día."""
    try:
        datos = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if datos.get("fecha") != _hoy():
        return {}
    return datos.get("veredictos", {})


def guardar_cache(veredictos: dict[str, dict]) -> None:
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(
            json.dumps({"fecha": _hoy(), "veredictos": veredictos},
                       ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as e:
        print(f"  (no pude guardar el caché de veredictos: {e})", file=sys.stderr)


def _pedir(lote: list[dict], sistema: str, modelo: str, llave: str,
           timeout: int, topes: int) -> tuple[list[dict], dict]:
    """Una llamada. Devuelve (objetos, uso de tokens).

    El bloque de criterios va marcado con cache_control: es idéntico en todas
    las llamadas, así que se cobra completo la primera vez y al 10% después.
    """
    payload = {
        "model": modelo,
        "max_tokens": topes,
        "system": [{
            "type": "text",
            "text": sistema,
            "cache_control": {"type": "ephemeral"},
        }],
        "messages": [{"role": "user", "content": json.dumps(lote, ensure_ascii=False)}],
    }
    respuesta = requests.post(
        API, json=payload, timeout=timeout,
        headers={
            "x-api-key": llave,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    texto = "".join(b.get("text", "") for b in datos.get("content", [])
                    if b.get("type") == "text").strip()
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        texto = texto[4:] if texto.startswith("json") else texto
    return json.loads(texto), datos.get("usage", {})


def _costo(uso: dict, modelo: str) -> float:
    """Estimación en dólares del gasto de la corrida."""
    entrada, salida = PRECIOS.get(modelo, (1.0, 5.0))
    nuevos = uso.get("input_tokens", 0)
    escritos = uso.get("cache_creation_input_tokens", 0)
    leidos = uso.get("cache_read_input_tokens", 0)
    return (
        nuevos * entrada
        + escritos * entrada * 1.25   # escribir el caché cuesta un poco más
        + leidos * entrada * 0.10     # leerlo cuesta el 10%
        + uso.get("output_tokens", 0) * salida
    ) / 1_000_000


def enriquecer(notas: list[dict], secciones: list[str], subsecciones: list[str],
               ajustes: dict) -> dict[str, dict]:
    """Devuelve {id: veredicto}. Diccionario vacío si la capa no está activa."""
    llave = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not llave:
        print("  (sin ANTHROPIC_API_KEY: se usa la clasificación por palabras clave)",
              file=sys.stderr)
        return {}
    if not notas:
        return {}

    try:
        criterios = CRITERIOS.read_text(encoding="utf-8")
    except OSError:
        print("  (no encontré criterios.md: se omite la curaduría)", file=sys.stderr)
        return {}

    sistema = INSTRUCCIONES.format(
        secciones=", ".join(f'"{s}"' for s in secciones),
        subsecciones=", ".join(f'"{s}"' for s in subsecciones),
        bloque_resumen=BLOQUE_RESUMEN if ajustes.get("resumenes_ia") else "",
        criterios=criterios,
    )

    modelo = ajustes.get("modelo_ia", "claude-haiku-4-5")
    tam = int(ajustes.get("lote_ia", 30))
    timeout = int(ajustes.get("timeout_ia", 120))
    hilos = int(ajustes.get("hilos_ia", 5))

    # Se manda solo lo indispensable de cada nota: menos tokens, menos costo.
    ligeras = [{"id": n["id"], "titulo": n["titulo"],
                "resumen": n.get("resumen") or None,
                "fuente": n.get("fuente", ""),
                "seccion_del_feed": n.get("seccion", "")}
               for n in notas]

    lotes = [ligeras[i:i + tam] for i in range(0, len(ligeras), tam)]

    # En paralelo: nueve llamadas en fila se pasaban del límite de tiempo del
    # workflow. Cada lote es independiente, así que no hay razón para esperar.
    veredictos: dict[str, dict] = {}
    fallos = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos) as pool:
        tareas = {pool.submit(_pedir, lote, sistema, modelo, llave, timeout): i
                  for i, lote in enumerate(lotes, 1)}
        for tarea in concurrent.futures.as_completed(tareas):
            numero = tareas[tarea]
            try:
                for v in tarea.result():
                    if isinstance(v, dict) and v.get("id"):
                        veredictos[v["id"]] = v
            except Exception as e:  # noqa: BLE001
                fallos += 1
                print(f"  ✗ lote {numero}: {type(e).__name__}: {e}", file=sys.stderr)

    print(f"  curaduría: {len(veredictos)}/{len(notas)} notas en {len(lotes)} lotes, "
          f"{fallos} con error", file=sys.stderr)
    return veredictos


def aplicar(nota: dict, veredicto: dict | None, secciones: set[str],
            subsecciones: set[str]) -> bool:
    """Escribe el veredicto sobre la nota. False si la nota debe descartarse.

    Cada campo se valida antes de usarse: si el modelo devuelve una sección
    que no existe, se ignora ese campo y se conserva lo que ya traía la nota.
    """
    if not veredicto:
        return True

    if veredicto.get("ruido") is True:
        return False

    seccion = veredicto.get("seccion")
    if seccion in secciones:
        nota["seccion"] = seccion

    sub = veredicto.get("subseccion")
    if sub in subsecciones:
        nota["subseccion_ia"] = sub

    try:
        prioridad = int(veredicto.get("prioridad", 3))
        nota["prioridad"] = min(5, max(1, prioridad))
    except (TypeError, ValueError):
        nota["prioridad"] = 3

    resumen = veredicto.get("resumen")
    if resumen and not nota.get("resumen"):
        nota["resumen"] = str(resumen).strip()
        nota["resumen_generado"] = True

    historia = veredicto.get("historia")
    if historia:
        nota["historia"] = str(historia).strip().lower()

    return True
