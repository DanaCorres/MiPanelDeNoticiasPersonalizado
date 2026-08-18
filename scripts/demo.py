#!/usr/bin/env python3
"""Llena el panel con titulares de ejemplo, sin salir a internet.

Sirve para ver cómo se verá el diseño antes de la primera descarga real:

    python scripts/demo.py
    python -m http.server -d docs 8000   # y abre http://localhost:8000
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

RAIZ = Path(__file__).resolve().parents[1]
CDMX = ZoneInfo("America/Mexico_City")

EJEMPLOS = {
    ("nacional", "politica"): [
        ("Así quedó el reparto de comisiones en San Lázaro", "Milenio"),
        ("La oposición pide comparecencia de la titular de Seguridad", "Excélsior"),
    ],
    ("nacional", "economia"): [
        ("El peso cierra la jornada con su mejor nivel del mes", "El Financiero"),
        ("Inflación anual se ubica por debajo del pronóstico de Banxico", "La Jornada"),
    ],
    ("nacional", "cdmx"): [
        ("La Línea 1 del Metro reabre su tramo poniente este lunes", "Uno TV"),
        ("Brugada anuncia nuevas rutas del Cablebús para el próximo año", "El País México"),
    ],
    ("nacional", "opinion"): [
        ("La reforma que nadie quiere discutir en voz alta", "La Jornada — Opinión"),
    ],
    ("nacional", "tecnologia"): [
        ("Telecomunicaciones: qué cambia con las nuevas reglas de espectro", "El País"),
    ],
    ("ia", "nyt"): [
        ("A.I. Data Centers Are Reshaping Small-Town Power Bills", "The New York Times"),
        ("Inside the Race to Put A.I. Agents to Work", "The New York Times"),
    ],
    ("ia", "otros"): [
        ("La UE afina el reglamento de IA para modelos de propósito general", "El País — Tecnología"),
        ("Startups de agentes autónomos levantan otra ronda millonaria", "TechCrunch — IA"),
    ],
    ("colombia", "dia"): [
        ("El Congreso agenda el debate de la reforma pensional", "El Tiempo"),
        ("Paro de transportadores completa su tercer día en el Valle", "Blu Radio"),
    ],
    ("argentina", "dia"): [
        ("El Gobierno confirma el nuevo esquema cambiario", "Clarín"),
        ("Provincias reclaman por la coparticipación", "El Destape"),
    ],
    ("espana", "dia"): [
        ("El Congreso aprueba el techo de gasto tras una votación reñida", "El Mundo"),
    ],
    ("espectaculos", "dia"): [
        ("La pareja del año confirma su ruptura con un comunicado breve", "TMZ"),
    ],
}


def main() -> int:
    config = yaml.safe_load((RAIZ / "fuentes.yaml").read_text(encoding="utf-8"))
    ahora = datetime.now(CDMX)

    panel = {}
    for clave, datos in config["secciones"].items():
        panel[clave] = {
            "titulo": datos["titulo"],
            "codigo": datos["codigo"],
            "grupos": {g: {"titulo": t, "articulos": []} for g, t in datos["grupos"].items()},
        }

    minutos = 12
    for (seccion, grupo), notas in EJEMPLOS.items():
        for i, (titulo, fuente) in enumerate(notas):
            minutos += 37
            panel[seccion]["grupos"][grupo]["articulos"].append({
                "id": f"demo-{seccion}-{grupo}-{i}",
                "titulo": titulo,
                "resumen": ("El dirigente aseguró que la coalición no incluirá a la "
                            "exalcaldesa y que el proyecto es incompatible con el suyo."),
                "url": "https://example.com",
                "fuente": fuente,
                "seccion": seccion,
                "fecha": (ahora - timedelta(minutes=minutos)).isoformat(),
            })

    documento = {
        "generado": ahora.isoformat(),
        "total": sum(len(n) for n in EJEMPLOS.values()),
        "secciones": panel,
        "fuentes": [{"nombre": f["nombre"], "url": f["url"], "estado": "ok",
                     "detalle": "demostración"} for f in config["fuentes"]],
    }

    salida = RAIZ / "docs" / "datos" / "noticias.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(documento, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Panel de demostración escrito en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
