#!/usr/bin/env python3
"""Revisa una por una las fuentes de fuentes.yaml y dice cuáles responden.

Corre esto la primera vez que clonas el repo y cada vez que agregas un medio:
las direcciones RSS cambian sin avisar y este es el modo rápido de saber cuál
se rompió.

    python scripts/verificar_fuentes.py
"""

from __future__ import annotations

import concurrent.futures
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recolectar import descargar  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    config = yaml.safe_load((RAIZ / "fuentes.yaml").read_text(encoding="utf-8"))
    fuentes = config["fuentes"]
    timeout = config["ajustes"]["timeout"]

    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        tareas = [pool.submit(descargar, f, timeout) for f in fuentes]
        for tarea in concurrent.futures.as_completed(tareas):
            fuente, entradas, error = tarea.result()
            resultados.append((fuente, len(entradas), error))

    resultados.sort(key=lambda r: (r[2] is None, r[0]["seccion"], r[0]["nombre"]))

    ancho = max(len(f["nombre"]) for f, _, _ in resultados) + 2
    print()
    for fuente, cuantos, error in resultados:
        marca = "✗" if error else "✓"
        detalle = error or f"{cuantos} titulares"
        print(f" {marca}  {fuente['nombre']:<{ancho}} {detalle}")
        if error:
            print(f"    {fuente['url']}")

    rotas = [f for f, _, e in resultados if e]
    print(f"\n {len(resultados) - len(rotas)} de {len(resultados)} fuentes responden.")
    if rotas:
        print(" Cambia o quita las direcciones marcadas con ✗ en fuentes.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
