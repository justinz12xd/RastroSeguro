"""Markdown rendering for executive reports."""

from __future__ import annotations

from typing import Any


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        "# Reporte ejecutivo — RastroSeguro",
        "",
        f"Generado: `{report.get('generated_at', '')}`",
        "",
        "## Resumen",
        "",
        f"- Total de siniestros analizados: **{summary.get('total_siniestros', 0)}**",
        f"- Casos rojos: **{summary.get('casos_rojos', 0)}** ({summary.get('porcentaje_rojo', 0)}%)",
        f"- Casos amarillos: **{summary.get('casos_amarillos', 0)}**",
        f"- Casos verdes: **{summary.get('casos_verdes', 0)}**",
        f"- Monto total reclamado: **{summary.get('monto_total_reclamado', 0)}**",
        f"- Monto en casos rojos: **{summary.get('monto_reclamado_casos_rojos', 0)}**",
        "",
    ]
    savings = report.get("ahorro_potencial_estimado", {})
    if savings:
        lines.extend([
            "## Ahorro potencial estimado",
            "",
            f"- Monto expuesto (rojos): **{savings.get('monto_expuesto_rojos', 0)}**",
            f"- Tasa prevención asumida: **{savings.get('tasa_prevencion_asumida', 0)}**",
            f"- Ahorro estimado: **{savings.get('ahorro_potencial_estimado', 0)}**",
            "",
            str(savings.get("nota_etica", "")),
            "",
        ])
    lines.extend([
        _table("Top casos críticos", report.get("top_casos", [])),
        _table("Riesgo por ramo", report.get("riesgo_por_ramo", [])),
        _table("Top proveedores", report.get("top_proveedores", [])),
        _table("Top ciudades", report.get("top_ciudades", [])),
        "## Nota ética",
        "",
        str(report.get("ethics_note", "")),
        "",
    ])
    return "\n".join(lines)


def _table(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"## {title}\n\nSin datos disponibles.\n"

    columns = list(rows[0].keys())
    output = [f"## {title}", "", "| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        output.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    output.append("")
    return "\n".join(output)
