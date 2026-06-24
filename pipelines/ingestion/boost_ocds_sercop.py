"""
Extracción COMPLETA de OCDS y SERCOP sin tocar ECU911/INEC.

Modo completo:
  - SERCOP: sanciones 2015–2026, múltiples patrones de URL,
    también inhabilitaciones y resoluciones
  - OCDS: búsquedas temáticas (hasta 50 pág/término) +
    búsquedas por RUC de proveedores sancionados

Uso:
    py -3 -m pipelines.ingestion.boost_ocds_sercop
"""
from __future__ import annotations

import csv
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "ecuador"
META_DIR = ROOT / "data" / "ecuador"

OCDS_SEARCH = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/search_ocds"
OCDS_SUPPLIER = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/search_ocds_by_supplier"
TIMEOUT = 90
RUC_RE = re.compile(r"\b\d{13}\b")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "RastroSeguro/2.0 full-extraction",
        "Accept": "application/json, text/html",
    })
    a = requests.adapters.HTTPAdapter(max_retries=3)
    s.mount("https://", a)
    s.mount("http://", a)
    return s


# ═══════════════════════════════════════════════════════════════════════════
#  SERCOP
# ═══════════════════════════════════════════════════════════════════════════

def _build_sercop_urls() -> dict[int, list[str]]:
    urls: dict[int, list[str]] = {}
    for y in range(2015, 2027):
        candidates = [
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones-{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/sanciones{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/sanciones-{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/sanciones-{y}/",
            f"https://portal.compraspublicas.gob.ec/sercop/sanciones{y}/",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Inhabilitaciones{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Inhabilitaciones-{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/inhabilitaciones-{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Resoluciones{y}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Resoluciones-{y}",
        ]
        urls[y] = candidates
    return urls


def _extract_razon_social(raw: str) -> str:
    patterns = [
        r"(?:al\s+proveedor|al\s+administrado|al\s+contratista)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s,.\-&]+?)(?:,?\s+con\s+(?:Registro|RUC|R\.U\.C))",
        r"(?:SANCIONAR|SUSPENDER|INHABILITAR)\s+.*?\s+(?:proveedor|contratista)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s,.\-&]+?)(?:,?\s+con)",
        r"(?:proveedor|contratista)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s,.\-&]{5,60}?)(?:,?\s+con\s+RUC)",
    ]
    for p in patterns:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(",. ")
    return ""


def _extract_plazo_dias(raw: str) -> str:
    for p in [
        r"(\d+)\s*\)\s*d[ií]as",
        r"plazo\s+de\s+(?:\w+\s+)*\((\d+)\)",
        r"por\s+(\d+)\s+d[ií]as",
        r"(\d+)\s+d[ií]as\s+(?:calendario|h[aá]biles)",
    ]:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _extract_date(text: str) -> str:
    for p in [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{1,2})\s+de\s+(\w+)\s+de[l]?\s+(\d{4})",
    ]:
        m = re.search(p, text)
        if m:
            if m.lastindex == 1:
                return m.group(1)
            months = {
                "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
                "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
                "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
            }
            mon = months.get(m.group(2).lower(), "")
            if mon:
                return f"{m.group(3)}-{mon}-{m.group(1).zfill(2)}"
    return ""


def _extract_motivo(raw: str) -> str:
    low = raw.lower()
    for keyword, label in [
        ("información falsa", "Información falsa / declaración errónea"),
        ("declaración errónea", "Información falsa / declaración errónea"),
        ("incumplido", "Incumplimiento contractual"),
        ("incumplimiento", "Incumplimiento contractual"),
        ("fallido", "Adjudicatario fallido"),
        ("no participó", "No participó / no presentó oferta"),
        ("no presentó", "No participó / no presentó oferta"),
        ("inhabilitad", "Inhabilitación"),
        ("suspensión", "Suspensión del RUP"),
        ("suspender", "Suspensión del RUP"),
    ]:
        if keyword in low:
            return label
    return ""


def _extract_tipo_sancion(raw: str) -> str:
    low = raw.lower()
    if "inhabilitación" in low or "inhabilitar" in low:
        return "Inhabilitación"
    if "suspensión" in low or "suspender" in low:
        return "Suspensión"
    if "multa" in low:
        return "Multa"
    if "amonestación" in low:
        return "Amonestación"
    return ""


def _parse_row(year: int, raw: str, url: str, pdf_url: str) -> dict[str, str]:
    rucs = RUC_RE.findall(raw)
    return {
        "year": str(year),
        "ruc": rucs[0] if rucs else "",
        "razon_social": _extract_razon_social(raw),
        "fecha_emision": _extract_date(raw),
        "estado": "Vigente" if "vigente" in raw.lower() else "",
        "tipo_sancion": _extract_tipo_sancion(raw),
        "plazo_dias": _extract_plazo_dias(raw),
        "motivo_corto": _extract_motivo(raw),
        "pdf_url": pdf_url,
        "source_url": url,
        "raw": raw[:2000],
    }


def scrape_sercop_full(session: requests.Session) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    sercop_urls = _build_sercop_urls()

    for year, urls in sorted(sercop_urls.items()):
        year_rows_before = len(rows)
        for url in urls:
            try:
                resp = session.get(url, timeout=TIMEOUT)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
            except requests.RequestException:
                continue

            # Tables
            for tr in soup.select("table tr"):
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
                if len(cells) < 2:
                    continue
                raw = " ".join(cells)
                if len(raw) < 30:
                    continue
                dedup_key = raw[:250]
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                pdf_a = tr.find("a", href=re.compile(r"\.pdf", re.I))
                pdf_url = urljoin(url, pdf_a["href"]) if pdf_a else ""
                rows.append(_parse_row(year, raw, url, pdf_url))

            # Non-table elements (p, li, div, span)
            for el in soup.find_all(["p", "li", "div", "span", "article"]):
                txt = el.get_text(" ", strip=True)
                if len(txt) < 50 or not RUC_RE.search(txt):
                    continue
                dedup_key = txt[:250]
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                pdf_a = el.find("a", href=re.compile(r"\.pdf", re.I))
                pdf_url = urljoin(url, pdf_a["href"]) if pdf_a else ""
                rows.append(_parse_row(year, txt, url, pdf_url))

            time.sleep(0.2)

        added = len(rows) - year_rows_before
        logger.info("SERCOP year=%d urls_tried=%d new_rows=%d", year, len(urls), added)

    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  OCDS
# ═══════════════════════════════════════════════════════════════════════════

THEMATIC_TERMS = [
    "seguro", "seguros", "siniestro", "siniestros",
    "vehiculo", "vehiculos", "automotor", "automotriz",
    "robo", "hurto", "accidente", "accidentes",
    "poliza", "polizas", "aseguradora", "aseguradoras",
    "taller", "talleres", "perito", "peritos", "peritaje",
    "reparacion vehicular", "daño vehicular",
    "colision", "indemnizacion", "cobertura vehicular",
    "grua", "avaluo", "auxilio vial",
]

OCDS_FIELDS = [
    "year_query", "query_type", "search_term", "supplier_ruc",
    "ocid", "id", "year", "month", "method", "internal_type",
    "locality", "region", "suppliers", "buyer", "amount",
    "date", "title", "description", "budget",
]


def _parse_ocds_item(
    item: dict, year_query: int, query_type: str,
    search_term: str = "", supplier_ruc: str = "",
) -> dict[str, Any]:
    return {
        "year_query": year_query,
        "query_type": query_type,
        "search_term": search_term,
        "supplier_ruc": supplier_ruc,
        "ocid": (item.get("ocid") or "").strip(),
        "id": item.get("id"),
        "year": item.get("year"),
        "month": item.get("month"),
        "method": item.get("method"),
        "internal_type": item.get("internal_type"),
        "locality": item.get("locality"),
        "region": item.get("region"),
        "suppliers": item.get("suppliers"),
        "buyer": item.get("buyer"),
        "amount": item.get("amount"),
        "date": item.get("date"),
        "title": item.get("title"),
        "description": (item.get("description") or "")[:500],
        "budget": item.get("budget"),
    }


def _ocds_paginate(
    session: requests.Session,
    params: dict,
    max_pages: int,
    seen_ocids: set[str],
    parse_kwargs: dict,
) -> list[dict[str, Any]]:
    """Paginate one OCDS query, returning new unique rows."""
    rows: list[dict[str, Any]] = []
    try:
        first = session.get(OCDS_SEARCH, params={**params, "page": 1}, timeout=TIMEOUT).json()
    except Exception:
        return rows

    total = first.get("total")
    api_pages = int(first.get("pages", 1) or 1)
    pages_to_fetch = min(max_pages, api_pages)

    if total is None or total == 0:
        return rows

    for p in range(1, pages_to_fetch + 1):
        try:
            data = first if p == 1 else session.get(
                OCDS_SEARCH, params={**params, "page": p}, timeout=TIMEOUT
            ).json()
        except Exception:
            break
        items = data.get("data", [])
        if not isinstance(items, list) or not items:
            break
        for item in items:
            ocid = (item.get("ocid") or "").strip()
            if not ocid or ocid in seen_ocids:
                continue
            seen_ocids.add(ocid)
            rows.append(_parse_ocds_item(item, **parse_kwargs))
        time.sleep(0.05)

    return rows


def fetch_ocds_complete(
    session: requests.Session,
    year_start: int,
    year_end: int,
    max_pages_thematic: int = 50,
    max_pages_supplier: int = 20,
    sercop_rucs: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_ocids: set[str] = set()

    # 1) Thematic queries
    for year in range(year_start, year_end + 1):
        for term in THEMATIC_TERMS:
            new = _ocds_paginate(
                session,
                params={"year": year, "search": term},
                max_pages=max_pages_thematic,
                seen_ocids=seen_ocids,
                parse_kwargs={
                    "year_query": year,
                    "query_type": "thematic",
                    "search_term": term,
                },
            )
            rows.extend(new)
            if new:
                logger.info(
                    "OCDS thematic year=%d term='%s' +%d (total %d)",
                    year, term, len(new), len(rows),
                )

    # 2) Supplier RUC queries
    if sercop_rucs:
        for year in range(year_start, year_end + 1):
            for ruc in sercop_rucs:
                new = _ocds_paginate(
                    session,
                    params={"year": year, "search": ruc},
                    max_pages=max_pages_supplier,
                    seen_ocids=seen_ocids,
                    parse_kwargs={
                        "year_query": year,
                        "query_type": "supplier_ruc",
                        "supplier_ruc": ruc,
                    },
                )
                rows.extend(new)
                if new:
                    logger.info(
                        "OCDS supplier year=%d ruc=%s +%d (total %d)",
                        year, ruc, len(new), len(rows),
                    )

    # 3) Year-sample (no search filter) to catch anything we missed
    for year in range(year_start, year_end + 1):
        new = _ocds_paginate(
            session,
            params={"year": year},
            max_pages=10,
            seen_ocids=seen_ocids,
            parse_kwargs={
                "year_query": year,
                "query_type": "year_sample",
                "search_term": "",
            },
        )
        rows.extend(new)
        if new:
            logger.info(
                "OCDS year_sample year=%d +%d (total %d)",
                year, len(new), len(rows),
            )

    return rows


# ═══════════════════════════════════════════════════════════════════════════
#  UTILS
# ═══════════════════════════════════════════════════════════════════════════

def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

SERCOP_FIELDS = [
    "year", "ruc", "razon_social", "fecha_emision", "estado",
    "tipo_sancion", "plazo_dias", "motivo_corto", "pdf_url", "source_url", "raw",
]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    session = _session()
    t0 = time.time()

    # ── SERCOP ────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("SERCOP sanciones/inhabilitaciones (2015-2026)")
    logger.info("=" * 60)
    sercop_rows = scrape_sercop_full(session)
    sercop_path = RAW_DIR / "sercop_sanciones_2021_2026.csv"
    n_sercop = write_csv(sercop_path, sercop_rows, SERCOP_FIELDS)
    rucs_validos = [r["ruc"] for r in sercop_rows if re.fullmatch(r"\d{13}", r.get("ruc", ""))]
    unique_rucs = sorted(set(rucs_validos))
    logger.info("SERCOP total: %d filas, %d RUC válidos, %d únicos", n_sercop, len(rucs_validos), len(unique_rucs))

    # ── OCDS ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("OCDS completo: temático (50 pág) + por proveedor sancionado")
    logger.info("=" * 60)
    ocds_rows = fetch_ocds_complete(
        session,
        year_start=2019,
        year_end=2026,
        max_pages_thematic=50,
        max_pages_supplier=20,
        sercop_rucs=unique_rucs,
    )
    ocds_path = RAW_DIR / "ocds_proveedores_2021_2026.csv"
    n_ocds = write_csv(ocds_path, ocds_rows, OCDS_FIELDS)
    logger.info("OCDS total: %d filas únicas", n_ocds)

    elapsed = time.time() - t0
    logger.info("=" * 60)
    logger.info("Terminado en %.1f minutos", elapsed / 60)

    # ── Resumen ───────────────────────────────────────────────────────────
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "sercop": {
            "rows": n_sercop,
            "rucs_validos": len(rucs_validos),
            "unique_rucs": len(unique_rucs),
            "years_covered": sorted(set(r["year"] for r in sercop_rows)),
            "path": str(sercop_path.relative_to(ROOT)),
        },
        "ocds": {
            "rows": n_ocds,
            "thematic_terms": len(THEMATIC_TERMS),
            "supplier_rucs_searched": len(unique_rucs),
            "years_covered": sorted(set(str(r.get("year", "")) for r in ocds_rows if r.get("year"))),
            "path": str(ocds_path.relative_to(ROOT)),
        },
    }
    summary_path = META_DIR / "boost_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("=" * 60)
    print(f"SERCOP: {sercop_path} ({n_sercop} filas, {len(unique_rucs)} RUCs únicos)")
    print(f"OCDS:   {ocds_path} ({n_ocds} filas únicas)")
    print(f"Tiempo: {elapsed / 60:.1f} minutos")
    print(f"Resumen: {summary_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
