"""Human-in-the-loop document extraction for one claim per PDF/TXT upload.

The implementation is intentionally conservative: embedded text/TXT are parsed
locally with evidence; scanned PDFs require the multimodal LLM configuration and
return an actionable error when it is unavailable. The output is a review object,
not an automated fraud decision.
"""

from __future__ import annotations

import base64
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

CANONICAL_FIELDS = [
    "id_siniestro",
    "id_poliza",
    "id_asegurado",
    "ramo",
    "cobertura",
    "fecha_ocurrencia",
    "fecha_reporte",
    "monto_reclamado",
    "monto_estimado",
    "suma_asegurada",
    "estado",
    "sucursal",
    "ciudad",
    "descripcion",
    "documentos_completos",
    "beneficiario",
    "id_proveedor",
    "monto_pagado",
    "dias_desde_inicio_poliza",
    "dias_desde_fin_poliza",
    "dias_entre_ocurrencia_reporte",
    "historial_siniestros_asegurado",
    "etiqueta_fraude_simulada",
    "fecha_inicio",
    "fecha_fin",
    "prima",
    "deducible",
    "canal_venta",
    "estado_poliza",
    "segmento",
    "antiguedad",
    "ciudad_asegurado",
    "numero_de_polizas",
    "reclamos_ultimos_12_meses",
    "mora_actual",
    "score_cliente_simulado",
    "tipo",
    "ciudad_proveedor",
    "reclamos_asociados",
    "monto_promedio_reclamado",
    "porcentaje_de_casos_observados",
    "antiguedad_proveedor",
]

CRITICAL_FIELDS = ["id_siniestro", "ramo", "fecha_ocurrencia", "fecha_reporte", "monto_reclamado"]
QUALITY_FIELDS = [
    "id_siniestro",
    "id_poliza",
    "id_asegurado",
    "ramo",
    "cobertura",
    "fecha_ocurrencia",
    "fecha_reporte",
    "monto_reclamado",
    "monto_estimado",
    "suma_asegurada",
    "estado",
    "sucursal",
    "ciudad",
    "descripcion",
    "documentos_completos",
    "beneficiario",
    "id_proveedor",
]
VALID_RAMOS = {"vida", "salud", "hogar", "vehiculos", "vehículos", "generales"}

FIELD_PATTERNS: dict[str, list[str]] = {
    "id_siniestro": [r"(?:id\s*)?siniestro\s*(?:n[º°o]\.?|nro\.?|#)?\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]*)", r"(?:nro\.?\s*)?reclamo\s*(?:n[º°o]\.?|#)?\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]*)", r"claim[_\s-]*id\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]*)"],
    "id_poliza": [r"(?:id\s*)?p[oó]liza\s*(?:n[º°o]\.?|nro\.?|#)?\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]*)", r"policy[_\s-]*id\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]*)"],
    "id_asegurado": [r"(?:id\s*)?asegurad[oa]\s*(?:n[º°o]\.?|nro\.?|#)?\s*[:#-]\s*([A-Z]{2,}[-_]\d+)", r"(?:id\s*)?asegurad[oa]\s*[:#-]\s*([^\n;]{2,80})", r"insured[_\s-]*id\s*[:#-]\s*([A-Z0-9_-]+)"],
    "ramo": [r"ramo\s*[:#-]\s*([^\n;]+)", r"l[ií]nea\s+(?:de\s+)?negocio\s*[:#-]\s*([^\n;]+)"],
    "cobertura": [r"cobertura\s*[:#-]\s*([^\n;]+)"],
    "fecha_ocurrencia": [r"fecha\s+(?:de\s+)?(?:ocurrencia|siniestro|evento)\s*[:#-]\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"],
    "fecha_reporte": [r"fecha\s+(?:de\s+)?(?:reporte|aviso|notificaci[oó]n)\s*[:#-]\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"],
    "monto_reclamado": [r"monto\s+reclamad[oa]\s*[:#-]?\s*(?:usd|us\$|\$|€|d[oó]lares?)?\s*([0-9][0-9.,]*)", r"valor\s+reclamad[oa]\s*[:#-]?\s*(?:usd|us\$|\$|€|d[oó]lares?)?\s*([0-9][0-9.,]*)", r"importe\s*[:#-]?\s*(?:usd|us\$|\$|€|d[oó]lares?)?\s*([0-9][0-9.,]*)"],
    "monto_estimado": [r"monto\s+estimad[oa]\s*[:#-]?\s*(?:usd|us\$|\$|€|d[oó]lares?)?\s*([0-9][0-9.,]*)"],
    "suma_asegurada": [r"suma\s+asegurada\s*[:#-]?\s*(?:usd|us\$|\$|€|d[oó]lares?)?\s*([0-9][0-9.,]*)"],
    "estado": [r"estado\s*[:#-]\s*([^\n;]+)"],
    "sucursal": [r"sucursal\s*[:#-]\s*([^\n;]+)"],
    "ciudad": [r"ciudad\s*[:#-]\s*([^\n;]+)"],
    "descripcion": [r"descripci[oó]n\s*[:#-]\s*([\s\S]{10,500})"],
    "documentos_completos": [r"documentos\s+completos\s*[:#-]\s*(s[ií]|no|true|false|completo|incompleto)"],
    "beneficiario": [r"beneficiari[oa]\s*[:#-]\s*([^\n;]+)"],
    "id_proveedor": [r"(?:id\s*)?proveedor\s*(?:n[º°o]\.?|nro\.?|#)?\s*[:#-]\s*([A-Z0-9][A-Z0-9_-]*)"],
}

PROMPT_INJECTION_PATTERNS = [
    r"ignora\s+(?:todas\s+)?(?:las\s+)?instrucciones",
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"act[uú]a\s+como",
    r"system\s*prompt",
    r"developer\s*message",
]

SENSITIVE_PATTERNS = [
    ("posible_cedula", r"(?:c[eé]dula|identificaci[oó]n|dni|ruc)\s*[:#-]?\s*\d{10,13}\b"),
    ("posible_tarjeta", r"(?:tarjeta|card|cuenta)\s*[:#-]?\s*(?:\d[ -]*?){13,16}\b"),
    ("posible_email", r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
]


@dataclass
class ExtractedText:
    text: str
    pages: list[dict[str, Any]]
    scanned_or_empty: bool = False


def allowed_document(filename: str) -> bool:
    return Path(filename.lower()).suffix in {".pdf", ".txt"}


def extract_document_review(filename: str, payload: bytes) -> dict[str, Any]:
    if not payload:
        raise ValueError("El documento está vacío.")
    if not allowed_document(filename):
        raise ValueError("El documento debe ser PDF o TXT para extracción inteligente.")

    suffix = Path(filename.lower()).suffix
    file_type = suffix.lstrip(".")
    extracted_text = _extract_text(file_type, payload)
    if file_type == "pdf" and extracted_text.scanned_or_empty and not _multimodal_llm_available():
        raise ValueError(
            "El PDF parece escaneado o no contiene texto embebido. "
            "Activa RASTRO_LLM_ENABLED=true y configura OPENAI_API_KEY para usar extracción multimodal."
        )

    text = extracted_text.text
    security_findings = _security_findings(text)
    document_profile = _classify_document(file_type, extracted_text)
    candidate_claims = _build_claim_candidates(text)
    if candidate_claims:
        first_candidate = candidate_claims[0]
        draft = first_candidate["claim"]
        evidence = first_candidate["field_evidence"]
    else:
        draft, evidence = _extract_fields(text)
    normalized = normalize_claim_payload(draft)
    consistency_findings = _consistency_findings(normalized, evidence)
    extraction_quality = _extraction_quality(normalized, evidence, consistency_findings, security_findings)
    overall_confidence = extraction_quality["score"]
    candidate_claims = [
        {
            **candidate,
            "claim": normalize_claim_payload(candidate["claim"]),
            "quality": _extraction_quality(
                normalize_claim_payload(candidate["claim"]),
                candidate["field_evidence"],
                _consistency_findings(normalize_claim_payload(candidate["claim"]), candidate["field_evidence"]),
                security_findings,
            ),
        }
        for candidate in candidate_claims[:25]
    ]

    mime = "application/pdf" if file_type == "pdf" else "text/plain"
    return {
        "document_id": f"DOC-{uuid.uuid4().hex[:12].upper()}",
        "filename": filename,
        "file_type": file_type,
        "document_profile": document_profile,
        "preview_base64": f"data:{mime};base64,{base64.b64encode(payload).decode('ascii')}",
        "extracted_claim": normalized,
        "field_evidence": evidence,
        "candidate_claims": candidate_claims,
        "security_findings": security_findings,
        "consistency_findings": consistency_findings,
        "overall_confidence": overall_confidence,
        "extraction_quality": extraction_quality,
        "requires_human_review": True,
        "pipeline_agents": [
            {"name": "Detector", "status": "ok", "detail": f"Tipo detectado: {document_profile['document_type']}."},
            {"name": "Extractor", "status": "ok", "detail": f"Documento convertido a {max(1, len(candidate_claims))} candidato(s)."},
            {"name": "Verificador de evidencia", "status": "ok", "detail": "Se enlazó cada campo con texto fuente cuando estuvo disponible."},
            {"name": "Filtro de seguridad", "status": "ok", "detail": "Contenido malicioso o sensible se marca como alerta, no como decisión automática."},
            {"name": "Normalizador", "status": "ok", "detail": "Valores adaptados al esquema de scoring."},
            {"name": "Validador de consistencia", "status": "ok", "detail": f"Calidad: {extraction_quality['verdict']}."},
        ],
    }


def normalize_claim_payload(claim: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {field: claim.get(field) for field in CANONICAL_FIELDS if claim.get(field) not in (None, "")}
    if "sucursal" in normalized and "ciudad" not in normalized:
        normalized["ciudad"] = normalized["sucursal"]
    if "monto_estimado" in normalized and "monto_reclamado" not in normalized:
        normalized["monto_reclamado"] = normalized["monto_estimado"]
    if "suma_asegurada" not in normalized and normalized.get("monto_reclamado") is not None:
        try:
            normalized["suma_asegurada"] = round(float(normalized["monto_reclamado"]) * 1.2, 2)
        except Exception:
            pass
    normalized.setdefault("documentos_completos", True)
    return normalized


def _classify_document(file_type: str, extracted_text: ExtractedText) -> dict[str, Any]:
    text = extracted_text.text or ""
    has_split_blocks = bool(re.search(r"Columnas\s+\d+\s+a\s+\d+", text, flags=re.IGNORECASE))
    has_table_headers = sum(1 for alias in HEADER_ALIASES if alias in _normalize_key(text)) >= 3
    has_label_values = len(re.findall(r"\b(?:siniestro|ramo|monto|fecha|p[oó]liza)\b\s*[:#-]", text, flags=re.IGNORECASE)) >= 2
    if extracted_text.scanned_or_empty:
        document_type = "pdf_escaneado_o_imagen"
    elif has_split_blocks:
        document_type = "tabla_pdf_por_bloques"
    elif has_table_headers:
        document_type = "tabla_pdf_digital"
    elif has_label_values:
        document_type = "formulario_o_carta"
    else:
        document_type = "texto_no_estructurado"
    return {
        "document_type": document_type,
        "text_chars": len(text),
        "line_count": len([line for line in text.splitlines() if line.strip()]),
        "has_text_layer": bool(text.strip()),
        "has_table_headers": has_table_headers,
        "has_split_column_blocks": has_split_blocks,
        "requires_ocr": extracted_text.scanned_or_empty,
        "methods_attempted": ["pdftotext_layout" if file_type == "pdf" else "txt_decode", "label_value_regex", "table_alias_mapper", "consistency_validator"],
    }


def _build_claim_candidates(text: str) -> list[dict[str, Any]]:
    fraudia_candidates = _extract_fraudia_split_table_candidates(text)
    if fraudia_candidates:
        return fraudia_candidates

    draft, evidence = _extract_fields(text)
    if not draft:
        return []
    confidence = _overall_confidence(evidence, _consistency_findings(draft, evidence), [])
    return [{
        "row_index": 0,
        "label": _candidate_label(draft, 0),
        "claim": draft,
        "field_evidence": evidence,
        "confidence": confidence,
        "method": "hibrido_local",
    }]


def _candidate_label(claim: dict[str, Any], index: int) -> str:
    claim_id = claim.get("id_siniestro") or f"fila {index + 1}"
    ramo = claim.get("ramo") or "sin ramo"
    amount = claim.get("monto_reclamado")
    amount_text = f" · ${amount}" if amount not in (None, "") else ""
    return f"{claim_id} · {ramo}{amount_text}"


def _extract_text(file_type: str, payload: bytes) -> ExtractedText:
    if file_type == "txt":
        text = payload.decode("utf-8", errors="replace")
        return ExtractedText(text=text, pages=[{"page": 1, "text": text}])
    return _extract_pdf_text(payload)


def _extract_pdf_text(payload: bytes) -> ExtractedText:
    poppler_text = _extract_pdf_text_with_pdftotext(payload)
    if poppler_text.text.strip():
        return poppler_text

    # Prefer optional PDF parsers when installed, but keep tests/dev lightweight.
    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader_cls = getattr(module, "PdfReader")
            from io import BytesIO
            reader = reader_cls(BytesIO(payload))
            pages = []
            for index, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append({"page": index, "text": page_text})
            text = "\n".join(page["text"] for page in pages).strip()
            return ExtractedText(text=text, pages=pages, scanned_or_empty=not bool(text))
        except Exception:
            continue
    # Fallback for simple/generated PDFs in tests: recover visible ASCII-ish text.
    decoded = payload.decode("latin-1", errors="ignore")
    visible = "\n".join(re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9_.,:$#/@()\- ]{8,}", decoded))
    visible = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in visible.splitlines() if line.strip())
    return ExtractedText(text=visible, pages=[{"page": 1, "text": visible}], scanned_or_empty=not bool(visible))


def _extract_pdf_text_with_pdftotext(payload: bytes) -> ExtractedText:
    """Extract layout-preserved PDF text using Poppler when available.

    Many analyst uploads are PDFs generated from spreadsheets. Regex-only
    extraction fails when fields are in table headers instead of label/value
    paragraphs, so `pdftotext -layout` is the best dependency-free local path
    in this environment.
    """

    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(payload)
            pdf_path = Path(tmp.name)
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", "-nopgbrk", str(pdf_path), "-"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            pdf_path.unlink(missing_ok=True)
        if result.returncode != 0:
            return ExtractedText(text="", pages=[{"page": 1, "text": ""}], scanned_or_empty=True)
        text = result.stdout.strip()
        return ExtractedText(text=text, pages=[{"page": 1, "text": text}], scanned_or_empty=not bool(text))
    except Exception:
        return ExtractedText(text="", pages=[{"page": 1, "text": ""}], scanned_or_empty=True)


def _extract_fields(text: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    draft: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []
    for field in CANONICAL_FIELDS:
        value = None
        source = ""
        for pattern in FIELD_PATTERNS.get(field, []):
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = _clean_value(field, match.group(1))
                source = _snippet(text, match.start(), match.end())
                break
        if value not in (None, ""):
            draft[field] = value
            evidence.append({
                "field": field,
                "value": value,
                "page": 1,
                "source_text": source,
                "confidence": 0.88,
                "inferred": False,
                "agent": "Extractor",
            })
    table_draft, table_evidence = _extract_table_fields(text)
    for field, value in table_draft.items():
        if field not in draft and value not in (None, ""):
            draft[field] = value
            evidence.append(table_evidence[field])
    if "descripcion" not in draft and text.strip():
        draft["descripcion"] = text.strip()[:400]
        evidence.append({
            "field": "descripcion",
            "value": draft["descripcion"],
            "page": 1,
            "source_text": text.strip()[:240],
            "confidence": 0.62,
            "inferred": True,
            "agent": "Extractor",
        })
    return draft, evidence


HEADER_ALIASES = {
    "id_siniestro": "id_siniestro",
    "siniestro": "id_siniestro",
    "claim_id": "id_siniestro",
    "id_poliza": "id_poliza",
    "poliza": "id_poliza",
    "id_asegurado": "id_asegurado",
    "asegurado": "id_asegurado",
    "ramo": "ramo",
    "cobertura": "cobertura",
    "fecha_ocurrencia": "fecha_ocurrencia",
    "fecha_reporte": "fecha_reporte",
    "monto_reclamado": "monto_reclamado",
    "monto_estimado": "monto_estimado",
    "suma_asegurada": "suma_asegurada",
    "estado": "estado",
    "sucursal": "sucursal",
    "ciudad": "ciudad",
    "descripcion": "descripcion",
    "documentos_completos": "documentos_completos",
    "beneficiario": "beneficiario",
    "id_proveedor": "id_proveedor",
    "proveedor": "id_proveedor",
}


def _extract_table_fields(text: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    fraudia_draft, fraudia_evidence = _extract_fraudia_split_table_fields(text)
    if fraudia_draft:
        return fraudia_draft, fraudia_evidence
    header_draft, header_evidence = _extract_header_table_fields(text)
    if header_draft:
        return header_draft, header_evidence
    return _infer_numeric_table_fields(text)


def _extract_fraudia_split_table_fields(text: str, row_index: int = 0) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Parse the legible Fraudia PDF format, whose columns are split by blocks.

    `data/fraudia_dataset_legible.pdf` renders one dataset across pages as
    "Columnas 1 a 8", "Columnas 9 a 16", etc. A generic table parser sees only
    the first block and misses monto_estimado, estado, sucursal, beneficiario,
    suma_asegurada and proveedor. This parser joins row N from each block into
    one canonical editable claim.
    """

    candidates = _extract_fraudia_split_table_candidates(text, max_candidates=row_index + 1)
    if row_index >= len(candidates):
        return {}, {}
    selected = candidates[row_index]
    return selected["claim"], {item["field"]: item for item in selected["field_evidence"]}


def _extract_fraudia_split_table_candidates(text: str, max_candidates: int = 25) -> list[dict[str, Any]]:
    if "Fraudia Dataset" not in text or "Columnas 1 a 8" not in text:
        return []

    sections = _fraudia_sections(text)
    block_1 = _parse_fraudia_block_1(sections.get("1 a 8", ""))
    if not block_1:
        return []

    rows_by_block = {
        "1 a 8": block_1,
        "9 a 16": _parse_fraudia_block_9_16(sections.get("9 a 16", "")),
        "17 a 24": _parse_fraudia_regular_block(sections.get("17 a 24", ""), [
            "dias_desde_fin_poliza",
            "dias_entre_ocurrencia_reporte",
            "historial_siniestros_asegurado",
            "etiqueta_fraude_simulada",
            "fecha_inicio",
            "fecha_fin",
            "prima",
            "suma_asegurada",
        ]),
        "25 a 32": _parse_fraudia_regular_block(sections.get("25 a 32", ""), [
            "deducible",
            "canal_venta",
            "ciudad",
            "estado_poliza",
            "segmento",
            "antiguedad",
            "ciudad_asegurado",
            "numero_de_polizas",
        ]),
        "33 a 40": _parse_fraudia_regular_block(sections.get("33 a 40", ""), [
            "reclamos_ultimos_12_meses",
            "mora_actual",
            "score_cliente_simulado",
            "id_proveedor",
            "tipo",
            "ciudad_proveedor",
            "reclamos_asociados",
            "monto_promedio_reclamado",
        ]),
        "41 a 42": _parse_fraudia_regular_block(sections.get("41 a 42", ""), [
            "porcentaje_de_casos_observados",
            "antiguedad_proveedor",
        ]),
    }

    row_count = min(max_candidates, max(len(rows) for rows in rows_by_block.values() if rows))
    candidates: list[dict[str, Any]] = []
    for row_index in range(row_count):
        merged: dict[str, Any] = {}
        evidence: list[dict[str, Any]] = []
        for block_name, rows in rows_by_block.items():
            if row_index >= len(rows):
                continue
            row, source = rows[row_index]
            for field, value in row.items():
                if value in (None, "") or field in merged:
                    continue
                merged[field] = value
                evidence.append(_table_evidence(field, value, source, confidence=0.92))
        if not merged:
            continue
        confidence = _overall_confidence(evidence, _consistency_findings(merged, evidence), [])
        candidates.append({
            "row_index": row_index,
            "label": _candidate_label(merged, row_index),
            "claim": merged,
            "field_evidence": evidence,
            "confidence": confidence,
            "method": "fraudia_split_column_blocks",
        })
    return candidates


def _fraudia_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"Columnas\s+(\d+\s+a\s+\d+)", text, flags=re.IGNORECASE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[re.sub(r"\s+", " ", match.group(1)).strip()] = text[start:end]
    return sections


def _parse_fraudia_block_1(section: str) -> list[tuple[dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], str]] = []
    pattern = re.compile(
        r"\b(SIN-\d+)\s+(POL-\d+)\s+(ASEG-\d+)\s+"
        r"(Vida|Salud|Hogar|Veh[ií]culos)\s+"
        r"(Responsabilidad\s+Civil|Choque|Incendio|Robo)\s+"
        r"(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})\s+([0-9.]+)",
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(section):
        source = match.group(0)
        rows.append(({
            "id_siniestro": match.group(1),
            "id_poliza": match.group(2),
            "id_asegurado": match.group(3),
            "ramo": match.group(4),
            "cobertura": match.group(5),
            "fecha_ocurrencia": match.group(6),
            "fecha_reporte": match.group(7),
            "monto_reclamado": _clean_value("monto_reclamado", match.group(8)),
        }, source))
    return rows


def _parse_fraudia_block_9_16(section: str) -> list[tuple[dict[str, Any], str]]:
    lines = [line.rstrip() for line in section.splitlines()]
    starts = [idx for idx, line in enumerate(lines) if re.match(r"^\s*\d+(?:\.\d+)?\s+\d+(?:\.\d+)?\s+", line)]
    rows: list[tuple[dict[str, Any], str]] = []
    state_values = ["Pago Parcial", "Pago Total", "Negativa", "Liquidado", "Reserva"]
    city_values = ["Guayaquil", "Ambato", "Quito", "Manta", "Cuenca"]
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        chunk_lines = [line.strip() for line in lines[start:end] if line.strip()]
        if not chunk_lines:
            continue
        chunk = " ".join(chunk_lines)
        first = chunk_lines[0]
        amount_match = re.match(r"^(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(.+)$", first)
        if not amount_match:
            continue
        rest = amount_match.group(3)
        state = next((value for value in state_values if rest.startswith(value)), "")
        if not state:
            continue
        after_state = rest[len(state):].strip()
        sucursal = next((value for value in city_values if after_state.startswith(value)), "")
        if not sucursal:
            continue
        description_start = after_state[len(sucursal):].strip()
        provider_match = re.search(r"\b(PROV-\d+)\b", chunk)
        days_match = re.search(r"\b(\d+)\s*$", chunk)
        docs_match = re.search(r"\b(S[ií]|No)\b(?=(?:\s+(?:fotogr[aá]fica|con|reportado|PROV-|c[aá]maras|inconsistencias)|\s*$))", chunk, flags=re.IGNORECASE)
        description_tail = " ".join(chunk_lines[1:])
        description = f"{description_start} {description_tail}".strip()
        description = re.sub(r"\bPROV-\d+\b", " ", description)
        description = re.sub(r"\b(S[ií]|No)\b\s*(?=fotogr[aá]fica|con|reportado|c[aá]maras|inconsistencias|robo|severos|$)", " ", description, flags=re.IGNORECASE)
        description = re.sub(r"\s+", " ", description).strip(" .")
        if days_match:
            description = re.sub(r"\s+\d+\s*$", "", description).strip()
        rows.append(({
            "monto_estimado": _clean_value("monto_estimado", amount_match.group(1)),
            "monto_pagado": _clean_value("monto_estimado", amount_match.group(2)),
            "estado": state,
            "sucursal": sucursal,
            "descripcion": description,
            "documentos_completos": _clean_value("documentos_completos", docs_match.group(1)) if docs_match else None,
            "beneficiario": provider_match.group(1) if provider_match else None,
            "dias_desde_inicio_poliza": int(days_match.group(1)) if days_match else None,
        }, chunk))
    return rows


def _parse_fraudia_regular_block(section: str, fields: list[str]) -> list[tuple[dict[str, Any], str]]:
    rows: list[tuple[dict[str, Any], str]] = []
    for line in [line.strip() for line in section.splitlines() if line.strip()]:
        if not re.match(r"^[\d.-]", line):
            continue
        values = _split_table_line(line)
        if len(values) != len(fields):
            continue
        row = {field: _clean_fraudia_value(field, value) for field, value in zip(fields, values)}
        rows.append((row, line))
    return rows


def _clean_fraudia_value(field: str, value: str) -> Any:
    if field in {"documentos_completos"}:
        return _clean_value(field, value)
    if field.startswith("fecha_"):
        return _normalize_date(value)
    if field in {
        "monto_estimado",
        "monto_pagado",
        "suma_asegurada",
        "prima",
        "deducible",
        "monto_promedio_reclamado",
        "porcentaje_de_casos_observados",
    }:
        return _clean_value("monto_estimado", value)
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value.strip()


def _extract_header_table_fields(text: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        headers = _split_table_line(line)
        canonical_headers = [_canonical_header(header) for header in headers]
        known_count = sum(1 for header in canonical_headers if header)
        if known_count < 3:
            continue
        for row_line in lines[index + 1 : index + 6]:
            values = _split_table_line(row_line)
            if len(values) < max(3, known_count // 2):
                continue
            draft: dict[str, Any] = {}
            evidence: dict[str, dict[str, Any]] = {}
            for position, field in enumerate(canonical_headers):
                if not field or position >= len(values) or field in draft:
                    continue
                value = _clean_value(field, values[position])
                if value in (None, ""):
                    continue
                draft[field] = value
                evidence[field] = _table_evidence(field, value, f"{line}\n{row_line}", confidence=0.86)
            if any(field in draft for field in CRITICAL_FIELDS):
                return draft, evidence
    return {}, {}


def _infer_numeric_table_fields(text: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Last-resort extraction for spreadsheet PDFs whose headers are not selectable.

    The visible PDF in the user's screenshot has table rows with dates and
    monetary amounts but no label/value text. We extract the first plausible row
    so the analyst gets an editable draft instead of an empty modal.
    """

    for line in [line.strip() for line in text.splitlines() if line.strip()]:
        dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", line)
        line_without_dates = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", line)
        money_values = [float(value.replace(",", "")) for value in re.findall(r"(?<![-\w])\d{3,}(?:\.\d{1,2})?\b", line_without_dates)]
        money_values = [value for value in money_values if value > 100]
        if len(dates) < 2 or not money_values:
            continue
        claim_id_match = re.search(r"\b(?:SIN[-_]?\d+|[A-Z]{2,}[-_]\d+)\b", line, flags=re.IGNORECASE)
        draft: dict[str, Any] = {
            "id_siniestro": claim_id_match.group(0).upper().replace("_", "-") if claim_id_match else f"DOC-{uuid.uuid4().hex[:8].upper()}",
            "ramo": "generales",
            "fecha_ocurrencia": dates[0],
            "fecha_reporte": dates[1],
            "monto_reclamado": money_values[0],
        }
        if len(money_values) > 1:
            draft["monto_estimado"] = money_values[1]
        if len(money_values) > 2:
            draft["suma_asegurada"] = money_values[2]
        draft["descripcion"] = "Fila tabular extraída del PDF. Revise y ajuste ramo/cobertura antes de confirmar."
        return {
            field: value for field, value in draft.items()
        }, {
            field: _table_evidence(field, value, line, confidence=0.58, inferred=field in {"id_siniestro", "ramo", "descripcion"})
            for field, value in draft.items()
        }
    return {}, {}


def _split_table_line(line: str) -> list[str]:
    if "," in line and line.count(",") >= 3:
        return [cell.strip().strip('"') for cell in line.split(",")]
    return [cell.strip() for cell in re.split(r"\s{2,}|\t+", line.strip()) if cell.strip()]


def _canonical_header(header: str) -> str | None:
    normalized = _normalize_key(header)
    return HEADER_ALIASES.get(normalized)


def _normalize_key(value: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    normalized = value.translate(replacements).lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized


def _table_evidence(field: str, value: Any, source: str, confidence: float, inferred: bool = False) -> dict[str, Any]:
    return {
        "field": field,
        "value": value,
        "page": 1,
        "source_text": source[:240],
        "confidence": confidence,
        "inferred": inferred,
        "agent": "Extractor tabular",
    }


def _clean_value(field: str, value: str) -> Any:
    cleaned = value.strip().strip('"').strip()
    if field in {"monto_reclamado", "monto_estimado", "suma_asegurada"}:
        parsed = _parse_amount(cleaned)
        return parsed if parsed is not None else cleaned
    if field == "documentos_completos":
        return cleaned.lower() in {"si", "sí", "true", "completo"}
    if field.startswith("fecha_"):
        return _normalize_date(cleaned)
    return re.split(r"\s{2,}|;", cleaned)[0].strip()


def _parse_amount(value: str) -> float | None:
    """Parse a money string into a float, tolerating currency tokens and both
    US (1,234.56 / 1725.82) and Latin/European (1.234,56 / 8.450,00) formats.
    """
    compact = re.sub(r"[^\d.,-]", "", value)
    if not re.search(r"\d", compact):
        return None
    has_comma = "," in compact
    has_dot = "." in compact
    if has_comma and has_dot:
        # The right-most separator is the decimal mark.
        if compact.rfind(",") > compact.rfind("."):
            compact = compact.replace(".", "").replace(",", ".")  # EU: dot=thousands
        else:
            compact = compact.replace(",", "")                     # US: comma=thousands
    elif has_comma:
        # Single comma with 1-2 trailing digits is a decimal mark; else thousands.
        if compact.count(",") == 1 and len(compact.split(",")[-1]) in (1, 2):
            compact = compact.replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif compact.count(".") > 1:
        compact = compact.replace(".", "")                         # 1.234.567 -> thousands
    elif "." in compact and len(compact.split(".")[-1]) == 3 and compact.count(".") == 1:
        # Single dot with exactly 3 trailing digits reads as a thousands group
        # (e.g. "8.450" -> 8450); 1-2 trailing digits stays decimal ("1725.82").
        compact = compact.replace(".", "")
    try:
        return float(compact)
    except ValueError:
        return None


def _normalize_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value


def _security_findings(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            findings.append({
                "code": "PROMPT_INJECTION",
                "severity": "alta",
                "message": "El documento contiene instrucciones dirigidas al sistema; fueron ignoradas.",
            })
            break
    for code, pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            findings.append({
                "code": code.upper(),
                "severity": "media",
                "message": "Se detectó posible dato personal/sensible en el documento. Revisión humana requerida.",
            })
    return findings


def _consistency_findings(claim: dict[str, Any], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    evidenced = {item["field"] for item in evidence}
    for field in CRITICAL_FIELDS:
        if claim.get(field) in (None, ""):
            findings.append({"field": field, "severity": "alta", "message": f"Falta campo crítico: {field}."})
        elif field not in evidenced and field != "id_siniestro":
            findings.append({"field": field, "severity": "media", "message": f"El campo {field} no tiene evidencia textual directa."})
    for field in ("monto_reclamado", "monto_estimado", "suma_asegurada"):
        if field in claim:
            try:
                if float(claim[field]) < 0:
                    findings.append({"field": field, "severity": "alta", "message": f"{field} no puede ser negativo."})
            except Exception:
                findings.append({"field": field, "severity": "media", "message": f"{field} debe ser numérico."})
    occurrence = claim.get("fecha_ocurrencia")
    report = claim.get("fecha_reporte")
    if occurrence and report:
        try:
            if datetime.fromisoformat(str(report)) < datetime.fromisoformat(str(occurrence)):
                findings.append({"field": "fecha_reporte", "severity": "alta", "message": "La fecha de reporte es anterior a la ocurrencia."})
        except Exception:
            findings.append({"field": "fecha_reporte", "severity": "media", "message": "No se pudieron validar las fechas."})
    ramo = str(claim.get("ramo") or "").strip().lower()
    if ramo and ramo not in VALID_RAMOS:
        findings.append({"field": "ramo", "severity": "media", "message": f"Ramo no reconocido: {claim.get('ramo')}."})
    if claim.get("monto_reclamado") not in (None, "") and claim.get("suma_asegurada") not in (None, ""):
        try:
            if float(claim["monto_reclamado"]) > float(claim["suma_asegurada"]):
                findings.append({"field": "monto_reclamado", "severity": "media", "message": "El monto reclamado supera la suma asegurada; revisar antes de confirmar."})
        except Exception:
            pass
    return findings


def _extraction_quality(
    claim: dict[str, Any],
    evidence: list[dict[str, Any]],
    consistency: list[dict[str, Any]],
    security: list[dict[str, Any]],
) -> dict[str, Any]:
    present_critical = [field for field in CRITICAL_FIELDS if claim.get(field) not in (None, "")]
    critical_ratio = len(present_critical) / len(CRITICAL_FIELDS)
    present_quality = [field for field in QUALITY_FIELDS if claim.get(field) not in (None, "")]
    completeness_ratio = len(present_quality) / len(QUALITY_FIELDS)
    evidenced = {item.get("field") for item in evidence if item.get("source_text")}
    evidence_ratio = len([field for field in present_quality if field in evidenced]) / max(1, len(present_quality))
    avg_field_confidence = sum(float(item.get("confidence", 0)) for item in evidence) / max(1, len(evidence))
    high_consistency = len([item for item in consistency if item.get("severity") == "alta"])
    medium_consistency = len([item for item in consistency if item.get("severity") == "media"])
    consistency_score = max(0.0, 1.0 - high_consistency * 0.22 - medium_consistency * 0.08)
    security_score = max(0.0, 1.0 - len(security) * 0.12)
    score = round(max(0.0, min(1.0,
        critical_ratio * 0.34
        + evidence_ratio * 0.22
        + completeness_ratio * 0.16
        + consistency_score * 0.16
        + avg_field_confidence * 0.08
        + security_score * 0.04
    )), 2)
    if score >= 0.85 and high_consistency == 0:
        verdict = "confiable"
    elif score >= 0.65:
        verdict = "requiere_revision"
    else:
        verdict = "baja_confianza"
    messages = []
    missing_critical = [field for field in CRITICAL_FIELDS if field not in present_critical]
    if missing_critical:
        messages.append(f"Faltan campos críticos: {', '.join(missing_critical)}.")
    if evidence_ratio < 0.8:
        messages.append("Algunos campos no tienen evidencia directa suficiente.")
    if high_consistency or medium_consistency:
        messages.append("Hay alertas de consistencia que deben revisarse antes del scoring.")
    if security:
        messages.append("Hay hallazgos de seguridad/PII; no se toma decisión automática.")
    if not messages:
        messages.append("Campos críticos completos, con evidencia y consistencia suficiente para revisión humana.")
    return {
        "score": score,
        "verdict": verdict,
        "critical_fields_present": len(present_critical),
        "critical_fields_total": len(CRITICAL_FIELDS),
        "fields_present": len(present_quality),
        "fields_expected": len(QUALITY_FIELDS),
        "evidence_coverage": round(evidence_ratio, 2),
        "completeness": round(completeness_ratio, 2),
        "consistency_score": round(consistency_score, 2),
        "security_score": round(security_score, 2),
        "average_field_confidence": round(avg_field_confidence, 2),
        "messages": messages,
    }


def _overall_confidence(evidence: list[dict[str, Any]], consistency: list[dict[str, Any]], security: list[dict[str, Any]]) -> float:
    if not evidence:
        return 0.0
    base = sum(float(item.get("confidence", 0)) for item in evidence) / len(evidence)
    penalty = 0.08 * len([item for item in consistency if item.get("severity") == "alta"]) + 0.05 * len(security)
    return round(max(0.0, min(1.0, base - penalty)), 2)


def _snippet(text: str, start: int, end: int) -> str:
    left = max(0, start - 80)
    right = min(len(text), end + 80)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def _multimodal_llm_available() -> bool:
    return os.environ.get("RASTRO_LLM_ENABLED", "false").lower() in {"1", "true", "yes", "on"} and bool(os.environ.get("OPENAI_API_KEY"))
