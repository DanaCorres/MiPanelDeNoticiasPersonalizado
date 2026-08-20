"""Capa de curaduría con la API de Claude (paso 4 del pipeline).

Qué hace, en una sola pasada por lote:
  - decide sección y subsección leyendo el titular, no la etiqueta del feed;
  - asigna prioridad de 1 a 5 según criterios.md;
  - escribe resumen para las notas que llegaron sin él (las de Google News);
  - marca las que son ruido de servicio.

Todo es opcional. Si no hay ANTHROPIC_API_KEY, si la API falla o si algo
viene mal formado, el recolector sigue con la clasificación por palabras
clave y el panel se publica igual. Nunca tumba la corrida.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
from pathlib import Path

import requests

API = "https://api.anthropic.com/v1/messages"
RAIZ = Path(__file__).resolve().parents[1]
CRITERIOS = RAIZ / "criterios.md"

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
  "resumen"    : dos líneas en español (máximo 40 palabras) con qué pasó, quién \
lo decidió y a quién afecta. Si la nota ya trae resumen propio, devuelve null. \
No interpretes, no adjetives, no completes lo que el titular no dice. Si el \
titular no alcanza para un resumen honesto, devuelve null.
  "historia"   : identificador corto en minúsculas y con guiones del hecho que \
narra la nota (ej. "renuncia-monica-soto-tepjf"). Dos notas del mismo hecho, \
aunque sean de medios distintos y con titulares distintos, deben compartir el \
mismo valor. Sirve para agrupar coberturas.

Responde ÚNICAMENTE con un arreglo JSON. Sin preámbulo, sin explicación, sin \
bloques de código. Un objeto por cada nota recibida, en el mismo orden.

--- CRITERIOS EDITORIALES ---
{criterios}
"""


def _pedir(lote: list[dict], sistema: str, modelo: str, llave: str,
           timeout: int) -> list[dict]:
    """Una llamada. Devuelve la lista de objetos o [] si algo sale mal."""
    payload = {
        "model": modelo,
        "max_tokens": 8000,
        "system": sistema,
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
    return json.loads(texto)


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
