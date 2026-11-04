"""Revisa que motor/ no use nada prohibido por el enunciado.

Uso: python tests/revisar_reglas.py
Busca en el código (con el módulo ast) dict, set, sorted, .sort(), min, max,
x in lista, .index(), .count() e imports fuera de csv, time y random.
"""

import ast
import pathlib
import sys

PERMITIDOS = {"csv", "time", "random"}
FUNCIONES_PROHIBIDAS = {"dict", "set", "frozenset", "sorted", "min", "max"}
METODOS_PROHIBIDOS = {"sort", "index", "count"}


def revisar(archivo):
    problemas = []
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        linea = getattr(nodo, "lineno", 0)
        if isinstance(nodo, (ast.Dict, ast.DictComp)):
            problemas.append((linea, "dict literal"))
        elif isinstance(nodo, (ast.Set, ast.SetComp)):
            problemas.append((linea, "set literal"))
        elif isinstance(nodo, ast.Compare):
            for op in nodo.ops:
                if isinstance(op, (ast.In, ast.NotIn)):
                    problemas.append((linea, "operador in"))
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            if isinstance(f, ast.Name) and f.id in FUNCIONES_PROHIBIDAS:
                problemas.append((linea, f.id + "()"))
            if isinstance(f, ast.Attribute) and f.attr in METODOS_PROHIBIDOS:
                problemas.append((linea, "." + f.attr + "()"))
        elif isinstance(nodo, ast.Import):
            for a in nodo.names:
                if a.name.split(".")[0] not in PERMITIDOS:
                    problemas.append((linea, "import " + a.name))
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level == 0 and nodo.module.split(".")[0] not in PERMITIDOS:
                problemas.append((linea, "from " + nodo.module + " import"))
    return problemas


def main():
    carpeta = pathlib.Path(__file__).resolve().parent.parent / "motor"
    total = 0
    for archivo in sorted(carpeta.glob("*.py")):
        for linea, que in revisar(archivo):
            print(f"{archivo.name}:{linea}: usa {que}")
            total += 1
    if total:
        print(f"{total} problema(s) encontrados")
        sys.exit(1)
    print("motor/ cumple las reglas")


if __name__ == "__main__":
    main()
