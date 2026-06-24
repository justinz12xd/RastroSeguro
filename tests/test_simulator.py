import csv
import tempfile
import unittest
from pathlib import Path

from src.simulator.context import load_historical_claims
from src.simulator.normalization import normalize_simulated_claim
from src.simulator.simulate_claim import simulate_new_claim


class SimulatorTest(unittest.TestCase):
    def test_normalize_simulated_claim_maps_ui_aliases(self):
        claim = normalize_simulated_claim({
            "id": "SIM-ALIAS",
            "ramo": "vehículo",
            "documentos_presentes": "no",
            "proveedor": "PROV-1",
            "relato": "Robo temprano",
            "monto_reclamado": "$9,500",
        })

        self.assertEqual(claim["id_siniestro"], "SIM-ALIAS")
        self.assertEqual(claim["ramo"], "vehiculos")
        self.assertFalse(claim["documentos_completos"])
        self.assertEqual(claim["id_proveedor"], "PROV-1")
        self.assertEqual(claim["descripcion"], "Robo temprano")
        self.assertEqual(claim["monto_reclamado"], 9500)

    def test_load_historical_claims_uses_csv_without_pandas(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.csv"
            with path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["id_siniestro", "monto_reclamado", "alertas_activadas"])
                writer.writeheader()
                writer.writerow({"id_siniestro": "SIN-1", "monto_reclamado": "1000", "alertas_activadas": "[]"})

            rows, context = load_historical_claims(path)

        self.assertTrue(context["historical_claims_loaded"])
        self.assertEqual(context["historical_claims_count"], 1)
        self.assertEqual(rows[0]["monto_reclamado"], 1000)
        self.assertNotIn("alertas_activadas", rows[0])

    def test_simulator_compares_against_historical_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.csv"
            with path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["id_siniestro", "ramo", "id_proveedor", "descripcion"])
                writer.writeheader()
                writer.writerow({
                    "id_siniestro": "SIN-HIST-1",
                    "ramo": "vehiculos",
                    "id_proveedor": "PROV-REPETIDO",
                    "descripcion": "Choque al salir del parqueadero sin testigos",
                })

            result = simulate_new_claim({
                "id_siniestro": "SIM-HIST-1",
                "ramo": "vehiculo",
                "tipo_evento": "choque",
                "id_proveedor": "PROV-REPETIDO",
                "descripcion": "Choque al salir del parqueadero sin testigos",
                "documentos_completos": False,
            }, data_path=path)

        self.assertTrue(result["context"]["historical_claims_loaded"])
        self.assertEqual(result["context"]["historical_claims_count"], 1)
        self.assertTrue(result["signals"]["graph"]["entidades_recurrentes"])
        self.assertTrue(result["signals"]["nlp"]["similares"])


if __name__ == "__main__":
    unittest.main()
