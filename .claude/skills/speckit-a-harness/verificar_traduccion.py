"""Check determinista: la traducción de tasks.md a plan.json no perdió nada.

La traducción la hace el modelo, porque tasks.md lo escribe otro modelo y su forma
varía; un parser sería frágil. Este script verifica lo que importa de ese juicio con
reglas baratas: cada tarea está en exactamente una fase, cada fase del plan traduce
una sola fase de tasks.md, cada FR está anclado, las fases de historia llevan su
Independent Test literal, las fases con pruebas exigen la evidencia en rojo y todas
las fases tienen gate humano.

Uso: python verificar_traduccion.py <carpeta_feature> <plan.json>
Exit 0 traducción válida, 1 errores (uno por línea), 2 uso o archivos inválidos.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FRASE_TEST_FIRST = ("Evidencia test-first: el `resultado.md` del primer intento de esta fase "
                    "(`.harness/tickets/<ticket_id>/<fase>/intento_1/resultado.md`) contiene, en una "
                    "sección `## Rojo`, la salida de `dotnet test` con las pruebas nuevas fallando, "
                    "antes de la implementación; los intentos siguientes lo referencian y no lo repiten")

RE_FASE = re.compile(r"^##\s+(?:Phase|Fase)\s+\d+\s*:\s*(.+?)\s*$", re.IGNORECASE)
RE_HISTORIA = re.compile(r"(?:User Story|Historia de usuario)\s+(\d+)", re.IGNORECASE)
RE_SUBSECCION_PRUEBAS = re.compile(r"^###\s+(?:Tests|Pruebas)\b", re.IGNORECASE)
RE_TAREA = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s*(T\d{3})\b")
RE_ETIQUETA_HISTORIA = re.compile(r"\[US(\d+)\]")
RE_ARCHIVO_PRUEBA = re.compile(r"tests[/\\]\S*Tests?\.cs\b")
RE_PASO = re.compile(r"^\s*(T\d{3})\b")
RE_FR_DEFINIDO = re.compile(r"^\s*[-*]\s*\**(FR-\d{3}[a-z]?)\**\s*:", re.MULTILINE)
RE_FR_ANCLADO = re.compile(r"spec\.md#(FR-\d{3}[a-z]?)$")
RE_FR_ID = re.compile(r"^FR-\d{3}[a-z]?$")
RE_SPEC_HISTORIA = re.compile(r"^###\s+User Story\s+(\d+)", re.IGNORECASE)
ETIQUETA_INDEPENDENT_TEST = "**Independent Test**:"


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def _fases_tasks(texto: str) -> tuple[list[dict], list[str]]:
    """(fases de tasks.md con tareas, tareas fuera de una fase reconocida).

    Cada fase: titulo, historia, tareas, con_pruebas. La historia sale del título o, si
    el título no la nombra, de las etiquetas [USn] de sus tareas.
    """
    fases: list[dict] = []
    huerfanas: list[str] = []
    actual: dict | None = None
    en_pruebas = False
    for linea in texto.splitlines():
        if linea.startswith("## "):
            encabezado = RE_FASE.match(linea)
            actual = None
            if encabezado:
                historia = RE_HISTORIA.search(encabezado.group(1))
                actual = {"titulo": encabezado.group(1),
                          "historia": int(historia.group(1)) if historia else None,
                          "tareas": [], "con_pruebas": False}
                fases.append(actual)
            en_pruebas = False
        elif linea.startswith("### "):
            en_pruebas = bool(RE_SUBSECCION_PRUEBAS.match(linea))
        else:
            tarea = RE_TAREA.match(linea)
            if not tarea:
                continue
            if actual is None:
                huerfanas.append(tarea.group(1))
                continue
            actual["tareas"].append(tarea.group(1))
            etiqueta = RE_ETIQUETA_HISTORIA.search(linea)
            if actual["historia"] is None and etiqueta:
                actual["historia"] = int(etiqueta.group(1))
            if en_pruebas or RE_ARCHIVO_PRUEBA.search(linea):
                actual["con_pruebas"] = True
    return [f for f in fases if f["tareas"]], huerfanas


def _independent_tests(spec: str) -> dict[int, str]:
    """{número de historia: texto normalizado de su Independent Test}."""
    resultado: dict[int, str] = {}
    historia: int | None = None
    lineas = spec.splitlines()
    for indice, linea in enumerate(lineas):
        if linea.startswith("#"):
            encabezado = RE_SPEC_HISTORIA.match(linea)
            historia = int(encabezado.group(1)) if encabezado else None
        elif historia is not None and linea.startswith(ETIQUETA_INDEPENDENT_TEST):
            parrafo = [linea[len(ETIQUETA_INDEPENDENT_TEST):]]
            for siguiente in lineas[indice + 1:]:
                if not siguiente.strip():
                    break
                parrafo.append(siguiente)
            resultado[historia] = _normalizar(" ".join(parrafo))
    return resultado


def _frs(spec: str) -> list[str]:
    return list(dict.fromkeys(RE_FR_DEFINIDO.findall(spec)))


def _tareas_de_pasos(fase: dict) -> list[str]:
    tareas = []
    for paso in fase.get("pasos") or []:
        coincidencia = RE_PASO.match(paso) if isinstance(paso, str) else None
        if coincidencia:
            tareas.append(coincidencia.group(1))
    return tareas


def _verificar_fase(fase: dict, fase_tasks: dict, independent_tests: dict[int, str],
                    errores: list[str]) -> None:
    fase_id = fase.get("id", "?")
    criterio = _normalizar(str(fase.get("criterio_exito") or ""))
    numero = fase_tasks["historia"]
    if numero is not None:
        literal = independent_tests.get(numero)
        if literal is None:
            errores.append(f"spec.md: User Story {numero} no tiene Independent Test")
        elif literal not in criterio:
            errores.append(f"{fase_id}: criterio_exito no contiene literal el Independent Test "
                           f"de User Story {numero}")
    if fase_tasks["con_pruebas"] and _normalizar(FRASE_TEST_FIRST) not in criterio:
        errores.append(f"{fase_id}: tiene pruebas y criterio_exito no trae la frase de "
                       f"evidencia test-first")


def verificar(carpeta_feature: Path, plan: dict) -> list[str]:
    carpeta = Path(carpeta_feature)
    spec = (carpeta / "spec.md").read_text(encoding="utf-8")
    fases_tasks, huerfanas = _fases_tasks((carpeta / "tasks.md").read_text(encoding="utf-8"))
    if not fases_tasks:
        return ["tasks.md: no se reconoce ninguna fase con tareas"]

    errores = [f"{tarea}: está fuera de una fase reconocida de tasks.md" for tarea in huerfanas]
    origen_de_tarea = {t: i for i, f in enumerate(fases_tasks) for t in f["tareas"]}
    independent_tests = _independent_tests(spec)
    fases_por_tarea: dict[str, list[str]] = {}
    anclados: set[str] = set()

    for fase in plan.get("fases") or []:
        fase_id = fase.get("id", "?")
        origenes: set[int] = set()
        for tarea in _tareas_de_pasos(fase):
            if tarea not in origen_de_tarea:
                errores.append(f"{fase_id}: el paso '{tarea}' no es una tarea de tasks.md")
                continue
            origenes.add(origen_de_tarea[tarea])
            ubicadas = fases_por_tarea.setdefault(tarea, [])
            if fase_id not in ubicadas:
                ubicadas.append(fase_id)

        if not origenes:
            errores.append(f"{fase_id}: no traduce ninguna fase de tasks.md")
        elif len(origenes) > 1:
            titulos = ", ".join(f"'{fases_tasks[i]['titulo']}'" for i in sorted(origenes))
            errores.append(f"{fase_id}: mezcla tareas de varias fases de tasks.md ({titulos})")
        else:
            _verificar_fase(fase, fases_tasks[origenes.pop()], independent_tests, errores)

        if (fase.get("prueba_manual") or {}).get("requerida") is not True:
            errores.append(f"{fase_id}: prueba_manual.requerida debe ser true (decisión 8)")

        for ancla in fase.get("anclajes") or []:
            fr = RE_FR_ANCLADO.search(str(ancla.get("ref", ""))) if isinstance(ancla, dict) else None
            if fr:
                anclados.add(fr.group(1))

    for tarea in origen_de_tarea:
        ubicadas = fases_por_tarea.get(tarea, [])
        if not ubicadas:
            errores.append(f"{tarea}: no aparece en ningún paso")
        elif len(ubicadas) > 1:
            errores.append(f"{tarea}: aparece en más de una fase ({', '.join(ubicadas)})")

    for indice, fuera in enumerate(plan.get("fuera_de_ejecucion") or []):
        ref = fuera.get("ref") if isinstance(fuera, dict) else None
        motivo = fuera.get("motivo") if isinstance(fuera, dict) else None
        if (not isinstance(ref, str) or not RE_FR_ID.match(ref)
                or not isinstance(motivo, str) or not motivo.strip()):
            errores.append(f"fuera_de_ejecucion[{indice}]: requiere ref FR-xxx y motivo no vacío")
            continue
        anclados.add(ref)

    for fr in _frs(spec):
        if fr not in anclados:
            errores.append(f"{fr}: no está anclado en ninguna fase ni en fuera_de_ejecucion")
    return errores


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("uso: python verificar_traduccion.py <carpeta_feature> <plan.json>", file=sys.stderr)
        return 2
    carpeta, ruta_plan = Path(argv[0]), Path(argv[1])
    for requerido in (carpeta / "spec.md", carpeta / "tasks.md", ruta_plan):
        if not requerido.is_file():
            print(f"no existe: {requerido}", file=sys.stderr)
            return 2
    try:
        plan = json.loads(ruta_plan.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f"{ruta_plan}: JSON inválido: {error}", file=sys.stderr)
        return 2

    errores = verificar(carpeta, plan)
    if errores:
        print("\n".join(errores))
        return 1
    fases_tasks, _ = _fases_tasks((carpeta / "tasks.md").read_text(encoding="utf-8"))
    tareas = sum(len(f["tareas"]) for f in fases_tasks)
    frs = len(_frs((carpeta / "spec.md").read_text(encoding="utf-8")))
    print(f"traducción: OK ({tareas} tareas, {frs} FR, {len(plan.get('fases') or [])} fases)")
    return 0


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main(sys.argv[1:]))
