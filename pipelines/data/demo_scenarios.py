"""Inject narrative clones and critical demo scenarios after signal application."""

from __future__ import annotations

import pandas as pd

from pipelines.data.claim_signals import SIGNAL_COLUMNS
from pipelines.data.ecuador_context import load_restricted_rucs


def ensure_generales_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all expected ramos are represented for dashboard and reto coverage."""
    out = df
    if len(out) >= 500:
        general_idx = out.index[::20]
        out.loc[general_idx, "ramo"] = "generales"
        out.loc[general_idx, "cobertura"] = "danio"
        out.loc[general_idx, "id_vehiculo"] = ""
        out.loc[general_idx, "placa_hash"] = ""
        out.loc[general_idx, "taller"] = ""
        out.loc[general_idx, "historial_siniestros_vehiculo"] = 0
        out.loc[general_idx, "tercero_identificado"] = True
        out.loc[general_idx, "conductor_recurrente"] = False
    return out


def inject_narrative_clones(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    clone_mask = out[SIGNAL_COLUMNS["monto_atipico"]] | out[SIGNAL_COLUMNS["documentos_inconsistentes"]]
    clone_indexes = out.index[clone_mask]
    templates = [
        "Vehículo impactado por tercero no identificado sin evidencia de cámaras en {ciudad}.",
        "Reporte de robo tardío con inconsistencias en factura y denuncia en {ciudad}.",
        "Reclamo recurrente con narrativa similar y proveedor observado en {ciudad}.",
    ]
    ciudades = out.loc[clone_indexes, "ciudad"]
    out.loc[clone_indexes, "descripcion"] = [
        templates[i % len(templates)].format(ciudad=ciudad)
        for i, ciudad in enumerate(ciudades)
    ]
    return out


def inject_critical_demo_cases(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if len(out) < 12:
        return out

    restricted_rucs = list(load_restricted_rucs())
    critical = out.head(12)
    for i, idx in enumerate(critical.index):
        out.at[idx, "ramo"] = "vehiculos"
        out.at[idx, "cobertura"] = "robo" if i % 2 == 0 else "choque"
        out.at[idx, "dias_desde_inicio_poliza"] = 1 + (i % 3)
        out.at[idx, "dias_entre_ocurrencia_reporte"] = 9 + (i % 7)
        out.at[idx, "documentos_completos"] = "No"
        out.at[idx, "documentos_inconsistentes"] = True
        out.at[idx, "tercero_identificado"] = False
        out.at[idx, "historial_siniestros_asegurado"] = 3 + (i % 3)
        out.at[idx, "historial_siniestros_vehiculo"] = 3 + (i % 2)
        out.at[idx, "conductor_recurrente"] = True
        if i % 3 == 1 and restricted_rucs:
            ruc = restricted_rucs[i % len(restricted_rucs)]
            out.at[idx, "supplier_ruc"] = ruc
            out.at[idx, "id_proveedor"] = f"PROV-{ruc}"
            out.at[idx, "beneficiario"] = f"PROV-RUC-{ruc}"
            out.at[idx, "lista_restrictiva_sercop"] = True
            out.at[idx, "descripcion"] = (
                f"Caso crítico demo {i + 1}: proveedor en lista restrictiva SERCOP en {out.at[idx, 'ciudad']}."
            )
        else:
            out.at[idx, "descripcion"] = (
                f"Caso crítico demo {i + 1}: siniestro de alto riesgo con patrón repetido en {out.at[idx, 'ciudad']}."
            )
        out.at[idx, "etiqueta_fraude_simulada"] = 1
    return out


def apply_demo_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    out = ensure_generales_coverage(df)
    out = inject_narrative_clones(out)
    return inject_critical_demo_cases(out)
