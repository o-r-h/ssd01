"""Pruebas del perfil ssd01 contra el motor de reglas real del harness.

El motor vive en producción (~/.claude/hooks/lib); aquí solo se importa, nunca
se modifica. Probar contra él, y no contra una copia de las regex, es lo que
garantiza que `excluir` y el filtro por extensión se comportan como en una fase.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PRODUCCION_HOOKS = Path.home() / ".claude" / "hooks"
CHECK_PRODUCCION = Path("C:/AZZULE/IA harness/profiles/editornotificaciones/checks/dotnet_build.py")

sys.path.insert(0, str(PRODUCCION_HOOKS))

from lib.checks import check_prohibited  # noqa: E402
from lib.contracts import resolve_check_names  # noqa: E402

API = "src/CuentasBancarias.Api/"


def _reglas() -> dict:
    return json.loads((RAIZ / ".claude" / "rules.json").read_text(encoding="utf-8"))


class ReglasDelPerfil(unittest.TestCase):
    def setUp(self):
        self.reglas = _reglas()

    def ids(self, ruta: str, linea: str) -> set[str]:
        return {h["id"] for h in check_prohibited(ruta, [(1, linea)], self.reglas)}

    def test_positivos_no_secretos(self):
        for ruta, linea in [(API + "Program.cs", 'options.ApiKey = "abc123";'),
                            (API + "appsettings.json", '"ApiKey": "clave-real"'),
                            (API + "appsettings.Development.json", '"Password": "x1"')]:
            self.assertIn("no_secretos", self.ids(ruta, linea), linea)

    def test_negativos_no_secretos(self):
        for linea in ['var clave = builder.Configuration["Auth:ApiKey"];',
                      '"ApiKey": ""', 'const string Header = "X-Api-Key";']:
            self.assertNotIn("no_secretos", self.ids(API + "Program.cs", linea), linea)
            self.assertNotIn("no_secretos", self.ids(API + "appsettings.json", linea), linea)

    def test_positivos_solo_dos_endpoints(self):
        for linea in ['app.MapDelete("/cuentas/{id}", h);', 'app.MapPut("/cuentas/{id}", h);',
                      'app.MapPatch("/cuentas/{id}", h);', 'app.MapGet("/health", h);',
                      'app.MapPost("/transferencias", h);', 'app.MapGet("/cuentasx", h);',
                      'app.MapMethods("/cuentas", new[] { "HEAD" }, h);']:
            self.assertIn("solo_dos_endpoints", self.ids(API + "Program.cs", linea), linea)

    def test_negativos_solo_dos_endpoints(self):
        for linea in ['app.MapPost("/cuentas", h);', 'app.MapGet("/cuentas/{id}", h);']:
            self.assertNotIn("solo_dos_endpoints", self.ids(API + "Program.cs", linea), linea)

    def test_dep_nueva_es_warning(self):
        hallazgos = check_prohibited(
            "src/X/X.csproj", [(1, '<PackageReference Include="Dapper" Version="2.1.35" />')],
            self.reglas)
        self.assertEqual([(h["id"], h["severidad"]) for h in hallazgos], [("dep_nueva", "warning")])

    def test_severidades(self):
        severidad = {r["id"]: r["severidad"] for r in self.reglas["prohibido"]}
        self.assertEqual(severidad, {"no_secretos": "error", "dep_nueva": "warning",
                                     "solo_dos_endpoints": "error"})

    def test_motor_respeta_excluir(self):
        linea = 'options.ApiKey = "clave-de-prueba";'
        self.assertEqual(self.ids("tests/CuentasBancarias.Tests/ApiFactory.cs", linea), set())
        self.assertEqual(self.ids(".claude/rules.json", '"ApiKey": "clave-real"'), set())
        self.assertEqual(self.ids("specs/001-x/contracts/ejemplo.json", '"ApiKey": "k1"'), set())
        self.assertEqual(self.ids("tests/CuentasBancarias.Tests/RutasTests.cs",
                                  'app.MapDelete("/x", h);'), set())

    def test_grupos_y_checks_resuelven(self):
        resueltos, desconocidos = resolve_check_names(["dotnet_build", "constitucion"], self.reglas)
        self.assertEqual(desconocidos, [])
        self.assertEqual(set(resueltos),
                         {"dotnet_build", "no_secretos", "dep_nueva", "solo_dos_endpoints"})
        self.assertEqual(self.reglas["perfil"], "ssd01")
        self.assertIs(self.reglas["audit_comments"]["requerido"], False)

    def test_dotnet_build_es_copia_exacta(self):
        local = (RAIZ / ".claude" / "checks" / "dotnet_build.py").read_bytes()
        self.assertEqual(local.replace(b"\r\n", b"\n"),
                         CHECK_PRODUCCION.read_bytes().replace(b"\r\n", b"\n"))


if __name__ == "__main__":
    unittest.main()
