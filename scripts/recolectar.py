#!/usr/bin/env python3
"""Descarga todos los feeds de fuentes.yaml y arma docs/datos/noticias.json.

Uso:
    python scripts/recolectar.py                # descarga real
    python scripts/recolectar.py --seccion ia   # solo una sección
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import feedparser
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from clasificar import clasificar_nacional, es_de_ia, normalizar  # noqa: E402
from criterios import aplicar_tope, es_tramite, reasignar_pais  # noqa: E402
from enriquecer import aplicar, enriquecer  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "fuentes.yaml"
SALIDA = RAIZ / "docs" / "datos" / "noticias.json"
CDMX = ZoneInfo("America/Mexico_City")

NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}

RASTREADORES = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                "utm_content", "cmpid", "smid", "partner", "ref", "fbclid"}


# --------------------------------------------------------------------------
# Descarga
# --------------------------------------------------------------------------


def descargar(fuente: dict, timeout: int) -> tuple[dict, list, str | None]:
    """Trae un feed. Devuelve (fuente, entradas, error)."""
    try:
        respuesta = requests.get(fuente["url"], headers=NAVEGADOR, timeout=timeout)
        respuesta.raise_for_status()
        feed = feedparser.parse(respuesta.content)
        if not feed.entries:
            return fuente, [], "el feed respondió pero llegó vacío"
        return fuente, feed.entries, None
    except requests.exceptions.HTTPError as e:
        return fuente, [], f"HTTP {e.response.status_code}"
    except requests.exceptions.Timeout:
        return fuente, [], f"sin respuesta en {timeout}s"
    except Exception as e:  # noqa: BLE001
        return fuente, [], f"{type(e).__name__}: {e}"


# --------------------------------------------------------------------------
# Limpieza de cada entrada
# --------------------------------------------------------------------------


def sin_html(texto: str) -> str:
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", unescape(texto)).strip()


def limpiar_url(url: str) -> str:
    partes = urlsplit(url or "")
    consulta = "&".join(
        p for p in partes.query.split("&")
        if p and p.split("=")[0].lower() not in RASTREADORES
    )
    return urlunsplit((partes.scheme, partes.netloc, partes.path, consulta, ""))


RUIDO = re.compile(
    r"(leer m[aá]s|seguir leyendo|contin[uú]a leyendo|the post .* appeared first on|"
    r"read more|\[\.\.\.\])\s*\.?$", re.IGNORECASE)


def limpiar_resumen(resumen: str, titulo: str) -> str:
    """Deja solo resúmenes que aporten algo.

    Muchos feeds repiten el titular en el resumen o meten un "Leer más". Vale
    más un renglón vacío que uno que no dice nada nuevo.
    """
    resumen = RUIDO.sub("", sin_html(resumen)).strip()
    if len(resumen) < 45:
        return ""

    corto_r, corto_t = normalizar(resumen)[:70], normalizar(titulo)[:70]
    if corto_r.startswith(corto_t[:50]) or corto_t.startswith(corto_r[:50]):
        return ""

    if len(resumen) > 230:
        resumen = resumen[:230].rsplit(" ", 1)[0].rstrip(",;:.") + "…"
    return resumen


def fecha_de(entrada) -> datetime | None:
    for campo in ("published_parsed", "updated_parsed", "created_parsed"):
        valor = entrada.get(campo)
        if valor:
            try:
                return datetime(*valor[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
    return None


def huella(titulo: str, url: str) -> str:
    """Identidad de una nota: sirve para no repetir la misma en dos medios."""
    base = re.sub(r"[^a-z0-9 ]", "", normalizar(titulo))
    base = " ".join(base.split()[:9])
    if len(base) < 12:
        base = limpiar_url(url)
    return hashlib.sha1(base.encode()).hexdigest()


def preparar(entrada, fuente: dict, ahora: datetime, horas_max: int,
             corte: datetime | None) -> dict | None:
    titulo = sin_html(entrada.get("title", ""))
    if len(titulo) < 12:
        return None

    url = limpiar_url(entrada.get("link", ""))
    if not url.startswith("http"):
        return None

    # Google Noticias manda el titular como "Titular - Medio". Se separa para
    # que el panel muestre quién lo publicó y no "Google Noticias" en todo.
    medio = fuente["nombre"]
    if "news.google.com" in url:
        origen = (entrada.get("source") or {}).get("title")
        if " - " in titulo:
            recorte, _, sufijo = titulo.rpartition(" - ")
            if len(sufijo) < 45 and len(recorte) > 20:
                titulo, origen = recorte, origen or sufijo
        if origen:
            medio = f"{origen} · vía Google"

    resumen = limpiar_resumen(entrada.get("summary", ""), titulo)
    fecha = fecha_de(entrada)
    if fecha and fecha > ahora + timedelta(hours=6):
        fecha = None  # fechas del futuro: error del medio, no del panel
    if fecha and (ahora - fecha) > timedelta(hours=horas_max):
        return None
    if corte and fecha and fecha < corte:
        return None  # es de ayer: el panel se reinició a medianoche
    if corte and not fecha:
        return None  # sin fecha no hay forma de saber si es de hoy

    return {
        "id": huella(titulo, url),
        "titulo": titulo,
        "resumen": resumen,
        "url": url,
        "fuente": medio,
        "seccion": fuente["seccion"],
        "fecha": fecha.isoformat() if fecha else None,
        "orden": (fecha or ahora - timedelta(hours=horas_max)).timestamp(),
    }


# --------------------------------------------------------------------------
# Armado del panel
# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Arma el panel de noticias.")
    parser.add_argument("--seccion", help="Procesa solo una sección")
    parser.add_argument("--salida", type=Path, default=SALIDA)
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    ajustes = config["ajustes"]
    secciones = config["secciones"]
    fuentes = [f for f in config["fuentes"]
               if not args.seccion or f["seccion"] == args.seccion]

    ahora = datetime.now(timezone.utc)
    horas_max = ajustes["horas_maximas"]

    # Reinicio diario: la medianoche de hoy en la Ciudad de México marca el
    # punto de partida. Todo lo anterior se queda fuera del panel.
    corte = None
    if ajustes.get("reinicio_diario"):
        corte = ahora.astimezone(CDMX).replace(
            hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)

    panel = {
        clave: {
            "titulo": datos["titulo"],
            "codigo": datos["codigo"],
            "grupos": {g: {"titulo": t, "articulos": []} for g, t in datos["grupos"].items()},
        }
        for clave, datos in secciones.items()
        if not args.seccion or clave == args.seccion
    }

    # La repetición se controla por sección: si una nota sale en El País y en
    # Milenio se muestra una sola vez, pero una portada compartida entre
    # "nacional" y "españa" sí puede aparecer en las dos.
    vistos: dict[str, set[str]] = {clave: set() for clave in panel}
    salud: list[dict] = []
    descartadas: list[dict] = []   # ruido de la regla 2, para poder auditarlo
    mudanzas = 0                   # notas que cambiaron de país (regla 1)

    # 1. Descarga en paralelo
    cosecha: list[tuple[dict, list]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=ajustes["hilos"]) as pool:
        tareas = [pool.submit(descargar, f, ajustes["timeout"]) for f in fuentes]
        for tarea in concurrent.futures.as_completed(tareas):
            fuente, entradas, error = tarea.result()
            salud.append({
                "nombre": fuente["nombre"],
                "url": fuente["url"],
                "estado": "error" if error else "ok",
                "detalle": error or f"{len(entradas)} titulares",
            })
            print(f"  {'✗' if error else '✓'} {fuente['nombre']}: "
                  f"{error or f'{len(entradas)} titulares'}", file=sys.stderr)
            if not error and fuente["seccion"] in panel:
                cosecha.append((fuente, entradas))

    # 2. Reparto, en orden fijo: primero los feeds que ya vienen etiquetados
    #    (La Jornada — Economía, por ejemplo) y luego las portadas generales.
    #    Así el panel sale igual aunque los feeds respondan en otro orden.
    cosecha.sort(key=lambda c: (
        0 if (c[0].get("subseccion") or c[0].get("grupo")) else 1, c[0]["nombre"]))

    # 2a. Se juntan todas las notas antes de repartirlas: la capa de curaduría
    #     necesita ver el lote completo para poder agrupar historias repetidas.
    candidatas: list[dict] = []
    for fuente, entradas in cosecha:
        for entrada in entradas:
            nota = preparar(entrada, fuente, ahora, horas_max, corte)
            if not nota:
                continue

            # Regla 2: los instructivos de servicio no entran. Este filtro por
            # palabras clave es la primera pasada; es gratis y quita el grueso
            # antes de gastar tokens. La curaduría afina lo que quede.
            if es_tramite(nota["titulo"], nota["resumen"]):
                descartadas.append({**nota, "motivo": "tramite"})
                continue

            # Regla 1: la sección la decide el contenido, no el feed.
            nota["seccion"] = reasignar_pais(
                nota["titulo"], nota["resumen"], fuente["seccion"])
            if nota["seccion"] != fuente["seccion"]:
                mudanzas += 1
            nota["_subseccion_feed"] = (
                fuente.get("subseccion") if nota["seccion"] == fuente["seccion"] else None)
            nota["_grupo_feed"] = fuente.get("grupo")
            candidatas.append(nota)

    # 2b. Curaduría con la API de Claude. Opcional: si no hay llave o falla,
    #     devuelve vacío y todo sigue con la clasificación por palabras clave.
    subsecciones_validas = set(secciones.get("nacional", {}).get("grupos", {}))
    veredictos = enriquecer(
        candidatas, list(panel), sorted(subsecciones_validas), ajustes)

    # 2c. Reparto
    for nota in candidatas:
        if not aplicar(nota, veredictos.get(nota["id"]),
                       set(panel), subsecciones_validas):
            descartadas.append({**nota, "motivo": "ruido (curaduría)"})
            continue

        seccion = nota["seccion"]
        if seccion not in panel or nota["id"] in vistos[seccion]:
            continue

        if seccion == "nacional":
            # Orden de mando: la curaduría, luego la subsección fija del feed,
            # y al final las palabras clave.
            grupo = (nota.pop("subseccion_ia", None)
                     or nota["_subseccion_feed"]
                     or clasificar_nacional(nota["titulo"], nota["resumen"], nota["url"]))
            if not grupo:
                continue
        elif seccion == "ia":
            if not es_de_ia(nota["titulo"], nota["resumen"], nota["url"]):
                continue
            grupo = nota["_grupo_feed"] or "otros"
        else:
            grupo = nota["_grupo_feed"] or "dia"
            if grupo not in panel[seccion]["grupos"]:
                grupo = next(iter(panel[seccion]["grupos"]))

        if grupo not in panel[seccion]["grupos"]:
            continue

        for campo in ("_subseccion_feed", "_grupo_feed", "subseccion_ia"):
            nota.pop(campo, None)
        vistos[seccion].add(nota["id"])
        panel[seccion]["grupos"][grupo]["articulos"].append(nota)

    # Ordena por fecha, aplica el tope por fuente y recorta
    tope = ajustes.get("tope_por_fuente", 0)
    for seccion in panel.values():
        for grupo in seccion["grupos"].values():
            # Con curaduría activa manda la prioridad y la hora desempata.
            # Sin ella, todas las notas valen 3 y el orden es cronológico.
            grupo["articulos"].sort(
                key=lambda n: (n.get("prioridad", 3), n["orden"]), reverse=True)
            grupo["articulos"] = aplicar_tope(grupo["articulos"], tope)
            del grupo["articulos"][ajustes["max_por_grupo"]:]
            for nota in grupo["articulos"]:
                nota.pop("orden", None)

    salud.sort(key=lambda f: (f["estado"] == "ok", f["nombre"]))
    total = sum(len(g["articulos"]) for s in panel.values() for g in s["grupos"].values())

    documento = {
        "generado": ahora.astimezone(CDMX).isoformat(),
        "desde": corte.astimezone(CDMX).isoformat() if corte else None,
        "total": total,
        "secciones": panel,
        "fuentes": salud,
    }

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps(documento, ensure_ascii=False, indent=1), encoding="utf-8")

    # Bitácora de lo que se descartó por ruido. No se muestra en el panel:
    # sirve para revisar si el criterio se está comiendo algo que sí querías.
    for nota in descartadas:
        nota.pop("orden", None)
    (args.salida.parent / "descartadas.json").write_text(
        json.dumps({"generado": documento["generado"], "notas": descartadas},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    fallas = sum(1 for f in salud if f["estado"] == "error")
    print(f"\n{total} titulares guardados en {args.salida}", file=sys.stderr)
    print(f"{len(salud) - fallas} fuentes vivas, {fallas} con problemas", file=sys.stderr)
    print(f"{len(descartadas)} descartadas por trámite, "
          f"{mudanzas} reasignadas de país", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
