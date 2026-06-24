"""Audit-ready report export (PDF §10.2)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.reports.markdown_report import render_markdown_report
from src.reports.savings_simulation import simulate_savings
from src.utils.serialization import from_json_list


def build_audit_report(claims: list[dict[str, Any]], top_limit: int = 20) -> dict[str, Any]:
    red = [c for c in claims if str(c.get("nivel_riesgo", "")).lower() == "rojo"]
    red_sorted = sorted(red, key=lambda c: float(c.get("score_final", 0) or 0), reverse=True)[:top_limit]

    missing_docs = [
        {
            "id_siniestro": c.get("id_siniestro"),
            "nivel_riesgo": c.get("nivel_riesgo"),
            "documentos_completos": c.get("documentos_completos"),
        }
        for c in red
        if str(c.get("documentos_completos", "")).lower() in {"no", "false", "0"}
    ]

    audit_cases = []
    for claim in red_sorted:
        alerts = from_json_list(claim.get("alertas_activadas") or claim.get("rule_trace"))
        audit_cases.append({
            "id_siniestro": claim.get("id_siniestro"),
            "score_final": claim.get("score_final"),
            "nivel_riesgo": claim.get("nivel_riesgo"),
            "monto_reclamado": claim.get("monto_reclamado"),
            "reglas_activadas": [a.get("code") for a in alerts if isinstance(a, dict)],
            "explicacion": claim.get("explicacion", ""),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_casos_rojos": len(red),
        "top_casos_auditoria": audit_cases,
        "documentos_faltantes_criticos": missing_docs[:top_limit],
        "ahorro_potencial": simulate_savings(claims),
        "ethics_note": (
            "Reporte de auditoría para revisión humana. RastroSeguro no acusa fraude "
            "ni rechaza reclamos automáticamente."
        ),
    }


def render_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Reporte de auditoría — RastroSeguro",
        "",
        f"Generado: `{report.get('generated_at', '')}`",
        "",
        f"- Casos rojos en portafolio: **{report.get('total_casos_rojos', 0)}**",
        "",
        "## Top casos para revisión",
        "",
    ]
    for case in report.get("top_casos_auditoria", []):
        rules = ", ".join(case.get("reglas_activadas") or []) or "N/A"
        lines.extend([
            f"### {case.get('id_siniestro')}",
            f"- Score: **{case.get('score_final')}** ({case.get('nivel_riesgo')})",
            f"- Monto reclamado: **{case.get('monto_reclamado')}**",
            f"- Reglas: {rules}",
            f"- Explicación: {case.get('explicacion', '')}",
            "",
        ])

    savings = report.get("ahorro_potencial", {})
    lines.extend([
        "## Ahorro potencial estimado",
        "",
        f"- Monto expuesto (rojos): **{savings.get('monto_expuesto_rojos', 0)}**",
        f"- Tasa prevención asumida: **{savings.get('tasa_prevencion_asumida', 0)}**",
        f"- Ahorro estimado: **{savings.get('ahorro_potencial_estimado', 0)}**",
        "",
        str(savings.get("nota_etica", "")),
        "",
        "## Nota ética",
        "",
        str(report.get("ethics_note", "")),
        "",
    ])
    return "\n".join(lines)
