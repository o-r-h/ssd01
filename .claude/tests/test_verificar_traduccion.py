"""Pruebas de verificar_traduccion.py: la traducción tasks.md → plan.json no pierde nada."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / ".claude" / "skills" / "speckit-a-harness"))

from verificar_traduccion import FRASE_TEST_FIRST, main, verificar  # noqa: E402

SPEC = """### User Story 1 - Crear (Priority: P1)

**Independent Test**: Se prueba creando
una cuenta válida.

### User Story 2 - Consultar (Priority: P1)

**Independent Test**: Se prueba sembrando una cuenta.

- **FR-001**: crear.
- **FR-002**: validar.
- **FR-002a**: recortar.
- **FR-013**: MUST NOT listar.
"""

TASKS = """## Phase 1: Setup
- [ ] T001 Crear solución en CuentasBancarias.slnx
## Phase 2: Foundational
- [ ] T002 Middleware en src/Api/Auth.cs
## Phase 3: User Story 1 - Crear (Priority: P1)
### Tests for User Story 1
- [ ] T003 [US1] Pruebas en tests/T/CrearCuentaTests.cs
- [ ] T004 [US1] Endpoint en src/Api/Program.cs (depends on T002)
## Phase 4: User Story 2 - Consultar (Priority: P1)
- [ ] T005 [US2] Endpoint en src/Api/Program.cs
## Phase 5: Polish
- [ ] T006 README
"""

PASO_FIJO = ("ESCRIBE intento_N/resultado.md con la evidencia, incluida la corrida en rojo "
             "si la fase tiene pruebas")


def _fase(numero: int, pasos: list[str], criterio: str, anclas: list[str] = ()) -> dict:
    return {
        "id": f"fase_{numero}",
        "titulo": f"Fase {numero}",
        "criterio_exito": criterio,
        "pasos": [*pasos, PASO_FIJO],
        "anclajes": [{"ref": f"specs/x/spec.md#{a}", "confianza": "verificado"} for a in anclas],
        "checks_deterministas": ["dotnet_build"],
        "herramientas_permitidas": ["Read"],
        "depende_de": [],
        "prueba_manual": {"requerida": True},
        "max_reintentos": 3,
    }


def plan_valido() -> dict:
    return {
        "ticket_id": "SSD-001",
        "perfil": "ssd01",
        "fases": [
            _fase(1, ["T001 Crear solución en CuentasBancarias.slnx"], "La solución compila."),
            _fase(2, ["T002 Middleware en src/Api/Auth.cs"], "Sin credencial responde 401."),
            _fase(3, ["T003 Pruebas en tests/T/CrearCuentaTests.cs",
                      "T004 Endpoint en src/Api/Program.cs (depends on T002)"],
                  "Se prueba creando una cuenta válida. " + FRASE_TEST_FIRST,
                  ["FR-001", "FR-002", "FR-002a"]),
            _fase(4, ["T005 Endpoint en src/Api/Program.cs"], "Se prueba sembrando una cuenta.",
                  ["FR-013"]),
            _fase(5, ["T006 README"], "README al día."),
        ],
    }


class VerificarTraduccion(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._tmp.name)
        self.escribir(SPEC, TASKS)
        self.plan = plan_valido()

    def tearDown(self):
        self._tmp.cleanup()

    def escribir(self, spec: str, tasks: str):
        (self.carpeta / "spec.md").write_text(spec, encoding="utf-8")
        (self.carpeta / "tasks.md").write_text(tasks, encoding="utf-8")

    def fase(self, numero: int) -> dict:
        return self.plan["fases"][numero - 1]

    def errores(self) -> list[str]:
        return verificar(self.carpeta, self.plan)

    def assertError(self, fragmento: str):
        errores = self.errores()
        self.assertTrue(any(fragmento in e for e in errores),
                        f"se esperaba {fragmento!r} en {errores}")

    def test_plan_valido(self):
        self.assertEqual(self.errores(), [])

    def test_tarea_ausente(self):
        self.fase(5)["pasos"] = [PASO_FIJO]
        self.assertError("T006: no aparece en ningún paso")

    def test_tarea_en_dos_fases(self):
        self.fase(3)["pasos"].insert(0, "T002 Middleware otra vez")
        self.assertError("T002: aparece en más de una fase")

    def test_paso_que_menciona_otra_tarea_no_cuenta(self):
        self.assertIn("depends on T002", self.fase(3)["pasos"][1])
        self.assertEqual(self.errores(), [])

    def test_tarea_inventada(self):
        self.fase(5)["pasos"].insert(0, "T099 Algo que no está en tasks.md")
        self.assertError("fase_5: el paso 'T099' no es una tarea")

    def test_fase_que_mezcla(self):
        primera, segunda = self.plan["fases"][0], self.plan["fases"].pop(1)
        primera["pasos"] = [primera["pasos"][0], segunda["pasos"][0], PASO_FIJO]
        self.assertError("mezcla tareas de varias fases")

    def test_fase_sin_tareas(self):
        self.plan["fases"].append(_fase(6, [], "Algo extra."))
        self.assertError("fase_6: no traduce ninguna fase")

    def test_fr_sin_anclar(self):
        self.fase(4)["anclajes"] = []
        self.assertError("FR-013: no está anclado")

    def test_fr_fuera_de_ejecucion_con_motivo(self):
        self.fase(4)["anclajes"] = []
        self.plan["fuera_de_ejecucion"] = [{"ref": "FR-013", "motivo": "negativo"}]
        self.assertEqual(self.errores(), [])

    def test_fr_fuera_de_ejecucion_sin_motivo(self):
        self.fase(4)["anclajes"] = []
        self.plan["fuera_de_ejecucion"] = [{"ref": "FR-013", "motivo": ""}]
        self.assertError("fuera_de_ejecucion[0]: requiere ref")

    def test_fr_con_sufijo_no_cubre_el_base(self):
        self.fase(3)["anclajes"] = [a for a in self.fase(3)["anclajes"]
                                    if not a["ref"].endswith("#FR-002")]
        self.assertError("FR-002: no está anclado")

    def test_criterio_sin_independent_test(self):
        self.fase(3)["criterio_exito"] = FRASE_TEST_FIRST
        self.assertError("fase_3: criterio_exito no contiene literal el Independent Test "
                         "de User Story 1")

    def test_independent_test_con_otro_salto_de_linea(self):
        self.fase(3)["criterio_exito"] = ("Se prueba\ncreando una  cuenta válida.\n"
                                          + FRASE_TEST_FIRST)
        self.assertEqual(self.errores(), [])

    def test_fase_con_pruebas_sin_frase(self):
        self.fase(3)["criterio_exito"] = "Se prueba creando una cuenta válida."
        self.assertError("fase_3: tiene pruebas")

    def test_fase_sin_pruebas_no_exige_frase(self):
        self.assertNotIn(FRASE_TEST_FIRST, self.fase(4)["criterio_exito"])
        self.assertEqual(self.errores(), [])

    def test_csproj_de_pruebas_no_es_tarea_de_prueba(self):
        self.escribir(SPEC, TASKS.replace("T001 Crear solución en CuentasBancarias.slnx",
                                          "T001 Crear tests/T/T.Tests.csproj"))
        self.assertEqual(self.errores(), [])

    def test_prueba_manual_no_requerida(self):
        self.fase(1)["prueba_manual"] = {"requerida": False}
        self.assertError("fase_1: prueba_manual.requerida debe ser true")

    def test_tasks_sin_fases(self):
        self.escribir(SPEC, "# Tasks\n")
        self.assertError("tasks.md: no se reconoce ninguna fase")

    def test_tareas_marcadas_x(self):
        marcado = TASKS
        for tarea in ("T001", "T002", "T003"):
            marcado = marcado.replace(f"- [ ] {tarea}", f"- [x] {tarea}")
        self.escribir(SPEC, marcado)
        self.assertEqual(self.errores(), [])

    def test_titulos_en_espanol(self):
        traducido = (TASKS.replace("## Phase 3: User Story 1 - Crear", "## Fase 3: Historia de usuario 1 - Crear")
                     .replace("### Tests for User Story 1", "### Pruebas de la historia 1"))
        self.escribir(SPEC, traducido)
        self.assertEqual(self.errores(), [])
        self.fase(3)["criterio_exito"] = "Se prueba creando una cuenta válida."
        self.assertError("fase_3: tiene pruebas")

    def test_main_codigos_de_salida(self):
        ruta_plan = self.carpeta / "plan.json"
        ruta_plan.write_text(json.dumps(self.plan, ensure_ascii=False), encoding="utf-8")
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            self.assertEqual(main([str(self.carpeta), str(ruta_plan)]), 0)
        self.assertIn("traducción: OK (6 tareas, 4 FR, 5 fases)", salida.getvalue())

        invalido = copy.deepcopy(self.plan)
        invalido["fases"][4]["pasos"] = [PASO_FIJO]
        ruta_plan.write_text(json.dumps(invalido, ensure_ascii=False), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(self.carpeta), str(ruta_plan)]), 1)

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main([]), 2)
            self.assertEqual(main([str(self.carpeta), str(self.carpeta / "no-existe.json")]), 2)


if __name__ == "__main__":
    unittest.main()
