"""
Scraping completo de fuentes públicas de Ecuador a CSV (2021-2026 por defecto).

Salidas principales:
- data/raw/ecuador/ecu911_<start>_<end>.csv
- data/raw/ecuador/inec_siniestros_<start>_<end>.csv
- data/raw/ecuador/sercop_sanciones_<start>_<end>.csv
- data/raw/ecuador/ocds_proveedores_<start>_<end>.csv
- data/ecuador/inventario_manifest.json
- data/ecuador/inventario_links.tsv
- data/ecuador/data_dictionary_ecuador.csv
- data/ecuador/qa_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
import zipfile
from io import BytesIO, StringIO
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from pipelines.ingestion.sources import CONFIRMED_SOURCES, DEFAULT_YEAR_END, DEFAULT_YEAR_START

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "data" / "ecuador"
RAW_DIR = ROOT / "data" / "raw" / "ecuador"

CKAN_BASE = "https://www.datosabiertos.gob.ec/api/3/action"
OCDS_SEARCH = "https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/search_ocds"

USER_AGENT = "RastroSeguro/1.1 (hackIAthon; datos publicos Ecuador)"
DEFAULT_TIMEOUT = 60
RUC_PATTERN = re.compile(r"\b\d{13}\b")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json, text/html"})
    return s


def _get_json(session: requests.Session, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _get_html(session: requests.Session, url: str) -> BeautifulSoup:
    resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _safe_text(content: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _extract_year(text: str) -> str:
    m = re.search(r"(20\d{2})", text)
    return m.group(1) if m else ""


def _extract_date(text: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else ""


def fetch_ckan_package(session: requests.Session, package_id: str) -> dict[str, Any]:
    data = _get_json(session, f"{CKAN_BASE}/package_show", {"id": package_id})
    if not data.get("success"):
        raise RuntimeError(f"CKAN package_show falló para {package_id}")
    result = data["result"]
    resources = []
    for res in result.get("resources", []):
        resources.append(
            {
                "id": res.get("id"),
                "name": res.get("name"),
                "format": (res.get("format") or "").upper(),
                "url": res.get("url"),
                "created": res.get("created"),
                "last_modified": res.get("last_modified"),
            }
        )
    return {
        "package_id": package_id,
        "title": result.get("title"),
        "organization": (result.get("organization") or {}).get("title"),
        "metadata_modified": result.get("metadata_modified"),
        "resource_count": len(resources),
        "resources": resources,
    }


def fetch_ckan_organization_packages(
    session: requests.Session, org: str, rows: int = 100
) -> list[dict[str, Any]]:
    data = _get_json(
        session,
        f"{CKAN_BASE}/package_search",
        {"fq": f"organization:{org}", "rows": rows},
    )
    if not data.get("success"):
        raise RuntimeError(f"CKAN package_search falló para org={org}")
    out = []
    for pkg in data["result"].get("results", []):
        out.append(
            {
                "name": pkg.get("name"),
                "title": pkg.get("title"),
                "metadata_modified": pkg.get("metadata_modified"),
                "tags": [t.get("name") for t in pkg.get("tags", [])],
                "resource_formats": sorted(
                    {r.get("format", "").upper() for r in pkg.get("resources", []) if r.get("format")}
                ),
            }
        )
    return out


def filter_resources_by_year(resources: list[dict[str, Any]], year_start: int, year_end: int) -> list[dict[str, Any]]:
    filtered = []
    for res in resources:
        name = f"{res.get('name', '')} {res.get('url', '')}"
        years = {int(y) for y in re.findall(r"(20\d{2})", name)}
        if not years or any(year_start <= y <= year_end for y in years):
            filtered.append(res)
    return filtered


def scrape_page_links(session: requests.Session, url: str, extensions: tuple[str, ...]) -> list[dict[str, str]]:
    soup = _get_html(session, url)
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin(url, href)
        low = full.lower()
        if not any(low.endswith(ext) or ext in low for ext in extensions):
            continue
        if full in seen:
            continue
        seen.add(full)
        links.append({"url": full, "text": (a.get_text() or "").strip()[:250]})
    return links


def scrape_sercop_sanciones(session: requests.Session, url: str) -> list[dict[str, str]]:
    soup = _get_html(session, url)
    rows: list[dict[str, str]] = []

    for tr in soup.select("table tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        row_text = " ".join(cells)
        rucs = RUC_PATTERN.findall(row_text)
        pdf_link = tr.find("a", href=re.compile(r"\.pdf", re.I))
        rows.append(
            {
                "raw": row_text[:1000],
                "ruc": rucs[0] if rucs else "",
                "fecha_emision": _extract_date(row_text),
                "estado": "Vigente" if "vigente" in row_text.lower() else "",
                "pdf_url": urljoin(url, pdf_link["href"]) if pdf_link else "",
                "source_page": url,
            }
        )

    if rows:
        return rows

    for p in soup.find_all(["p", "li", "div"]):
        text = p.get_text(" ", strip=True)
        if len(text) < 40:
            continue
        rucs = RUC_PATTERN.findall(text)
        if not rucs:
            continue
        rows.append(
            {
                "raw": text[:1000],
                "ruc": rucs[0],
                "fecha_emision": _extract_date(text),
                "estado": "Vigente" if "vigente" in text.lower() else "",
                "pdf_url": "",
                "source_page": url,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


def extract_ecu911(
    session: requests.Session, year_start: int, year_end: int, output_csv: Path
) -> dict[str, Any]:
    meta = fetch_ckan_package(session, "base-de-emergencias")
    resources = filter_resources_by_year(meta.get("resources", []), year_start, year_end)
    csv_resources = []
    for r in resources:
        name = (r.get("name") or "").lower()
        url = (r.get("url") or "").lower()
        if "base de emergencias" in name and ".csv" in url:
            csv_resources.append(r)
    csv_resources.sort(key=lambda x: x.get("name") or "")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    files_ok = 0
    files_fail = 0
    header_written = False
    year_counter: dict[str, int] = {}

    with output_csv.open("w", encoding="utf-8", newline="") as out_f:
        for res in csv_resources:
            url = res.get("url") or ""
            name = res.get("name") or ""
            try:
                resp = session.get(url, timeout=120)
                resp.raise_for_status()
                text = _safe_text(resp.content).replace("\r\n", "\n").replace("\r", "\n")
                lines = [ln for ln in text.split("\n") if ln != ""]
                if not lines:
                    continue
                if header_written:
                    data_lines = lines[1:] if len(lines) > 1 else []
                    if data_lines:
                        out_f.write("\n".join(data_lines))
                        out_f.write("\n")
                        total_rows += len(data_lines)
                else:
                    out_f.write("\n".join(lines))
                    out_f.write("\n")
                    total_rows += max(0, len(lines) - 1)
                    header_written = True
                files_ok += 1
                y = _extract_year(name + " " + url)
                if y:
                    year_counter[y] = year_counter.get(y, 0) + max(0, len(lines) - 1)
            except requests.RequestException as exc:
                files_fail += 1
                logger.warning("ECU911 fallo %s: %s", url, exc)

    return {
        "metadata": meta,
        "resources_in_range": resources,
        "csv_resources_used": csv_resources,
        "output_csv": str(output_csv.relative_to(ROOT)),
        "files_ok": files_ok,
        "files_fail": files_fail,
        "rows": total_rows,
        "rows_by_year": year_counter,
    }


def extract_inec(session: requests.Session, output_csv: Path) -> dict[str, Any]:
    pages = {
        "anual": "https://www.ecuadorencifras.gob.ec/estadisticas-siniestros-de-transito/",
        "trimestral": "https://www.ecuadorencifras.gob.ec/siniestros-transito-trimestral/",
        "bases": "https://www.ecuadorencifras.gob.ec/estadistica-de-transporte-bases-de-datos/",
    }
    rows: list[dict[str, Any]] = []
    manifest_detail: dict[str, Any] = {}

    for key, page_url in pages.items():
        page_info: dict[str, Any] = {"page": page_url}
        try:
            soup = _get_html(session, page_url)
            table_count = 0
            for t_idx, table in enumerate(soup.find_all("table"), start=1):
                for r_idx, tr in enumerate(table.find_all("tr"), start=1):
                    cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                    if not cells:
                        continue
                    for c_idx, val in enumerate(cells, start=1):
                        rows.append(
                            {
                                "record_type": "table_cell",
                                "page_key": key,
                                "page_url": page_url,
                                "table_index": t_idx,
                                "row_index": r_idx,
                                "col_index": c_idx,
                                "value": val[:1200],
                                "link_url": "",
                                "link_text": "",
                            }
                        )
                    table_count += 1
            links = scrape_page_links(
                session,
                page_url,
                (".pdf", ".csv", ".xlsx", ".xls", ".zip", ".spss"),
            )
            for lk in links:
                rows.append(
                    {
                        "record_type": "download_link",
                        "page_key": key,
                        "page_url": page_url,
                        "table_index": "",
                        "row_index": "",
                        "col_index": "",
                        "value": "",
                        "link_url": lk.get("url", ""),
                        "link_text": lk.get("text", ""),
                    }
                )
            page_info["tables"] = table_count
            page_info["links"] = len(links)
            # Materializar tabulados descargables para que INEC no quede solo en links.
            parsed_cells = 0
            for lk in links:
                link_url = lk.get("url", "")
                low = link_url.lower()
                if ".csv" in low or low.endswith(".zip"):
                    parsed_cells += _materialize_inec_download(session, key, page_url, link_url, rows)
            page_info["download_data_cells"] = parsed_cells
            time.sleep(0.4)
        except requests.RequestException as exc:
            page_info["error"] = str(exc)
        manifest_detail[key] = page_info

    row_count = write_csv(
        output_csv,
        rows,
        [
            "record_type",
            "page_key",
            "page_url",
            "table_index",
            "row_index",
            "col_index",
            "value",
            "link_url",
            "link_text",
        ],
    )
    return {"output_csv": str(output_csv.relative_to(ROOT)), "rows": row_count, "pages": manifest_detail}


def _materialize_inec_download(
    session: requests.Session,
    page_key: str,
    page_url: str,
    link_url: str,
    rows: list[dict[str, Any]],
) -> int:
    """
    Descarga recursos INEC CSV/ZIP y los serializa en formato celda.
    Evita acoplarse a un esquema fijo porque los tabulados cambian por año.
    """
    added = 0
    try:
        resp = session.get(link_url, timeout=120)
        resp.raise_for_status()
        content = resp.content
    except requests.RequestException:
        return 0

    def append_csv_cells(source_name: str, csv_text: str) -> int:
        local_added = 0
        reader = csv.reader(StringIO(csv_text))
        for r_idx, row in enumerate(reader, start=1):
            for c_idx, value in enumerate(row, start=1):
                rows.append(
                    {
                        "record_type": "download_data_cell",
                        "page_key": page_key,
                        "page_url": page_url,
                        "table_index": source_name,
                        "row_index": r_idx,
                        "col_index": c_idx,
                        "value": str(value)[:1200],
                        "link_url": link_url,
                        "link_text": source_name,
                    }
                )
                local_added += 1
        return local_added

    low = link_url.lower()
    if low.endswith(".zip"):
        try:
            with zipfile.ZipFile(BytesIO(content)) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(".csv"):
                        try:
                            csv_bytes = zf.read(name)
                            csv_text = _safe_text(csv_bytes)
                            added += append_csv_cells(name, csv_text)
                        except Exception:
                            continue
        except Exception:
            return added
    elif ".csv" in low:
        csv_text = _safe_text(content)
        added += append_csv_cells(Path(link_url).name or "inec_csv", csv_text)
    return added


def extract_sercop(
    session: requests.Session, year_start: int, year_end: int, output_csv: Path
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    yearly: dict[str, Any] = {}
    for year in range(year_start, year_end + 1):
        urls = [
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones{year}",
            f"https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones-{year}",
        ]
        loaded = False
        for candidate in urls:
            try:
                extracted = scrape_sercop_sanciones(session, candidate)
                if not extracted:
                    continue
                for r in extracted:
                    r["year"] = year
                rows.extend(extracted)
                yearly[str(year)] = {"url": candidate, "rows": len(extracted)}
                loaded = True
                break
            except requests.RequestException:
                continue
        if not loaded:
            yearly[str(year)] = {"error": "No disponible"}

    unique_rows = []
    seen = set()
    for r in rows:
        key = (r.get("ruc", ""), r.get("raw", ""), r.get("source_page", ""))
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(r)

    row_count = write_csv(
        output_csv,
        unique_rows,
        ["year", "ruc", "fecha_emision", "estado", "pdf_url", "source_page", "raw"],
    )
    ruc_valid = sum(1 for r in unique_rows if re.fullmatch(r"\d{13}", (r.get("ruc") or "").strip()))
    return {
        "output_csv": str(output_csv.relative_to(ROOT)),
        "rows": row_count,
        "yearly": yearly,
        "ruc_valid_13": ruc_valid,
        "unique_ruc_count": len({r.get("ruc") for r in unique_rows if r.get("ruc")}),
        "unique_rucs": sorted({r.get("ruc") for r in unique_rows if r.get("ruc")}),
    }


def fetch_ocds_page(session: requests.Session, year: int, page: int, **extra: str) -> dict[str, Any]:
    params = {"year": year, "page": page}
    params.update({k: v for k, v in extra.items() if v})
    return _get_json(session, OCDS_SEARCH, params)


def extract_ocds(
    session: requests.Session,
    year_start: int,
    year_end: int,
    sancion_rucs: list[str],
    output_csv: Path,
    max_supplier_pages: int = 20,
    max_search_pages: int = 20,
    enable_supplier_queries: bool = True,
    enable_thematic_queries: bool = True,
) -> dict[str, Any]:
    """
    Extrae OCDS orientado a proveedores:
    1) muestra anual general (página 1 por año),
    2) consulta por proveedor (RUC sancionado) para captar su historial.
    """
    rows: list[dict[str, Any]] = []
    detail: dict[str, Any] = {}
    ocid_seen: set[str] = set()

    # Muestra anual base por año
    for year in range(year_start, year_end + 1):
        yr = {"sample_page_rows": 0, "total_hint": 0, "supplier_queries": 0}
        try:
            d = fetch_ocds_page(session, year=year, page=1)
            yr["total_hint"] = d.get("total", 0)
            for item in d.get("data", []):
                ocid = (item.get("ocid") or "").strip()
                if not ocid or ocid in ocid_seen:
                    continue
                ocid_seen.add(ocid)
                rows.append(
                    {
                        "year_query": year,
                        "query_type": "year_sample",
                        "query_supplier_ruc": "",
                        "ocid": ocid,
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
                        "description": item.get("description"),
                        "budget": item.get("budget"),
                    }
                )
            yr["sample_page_rows"] = len(d.get("data", []))
        except requests.RequestException as exc:
            yr["sample_error"] = str(exc)
        detail[str(year)] = yr

    # Búsqueda temática de seguros/siniestros para aumentar cobertura relevante.
    if enable_thematic_queries:
        thematic_terms = ("seguro", "seguros", "siniestro", "vehiculo", "vehículos", "robo", "accidente")
        for year in range(year_start, year_end + 1):
            detail[str(year)]["thematic_queries"] = 0
            for term in thematic_terms:
                try:
                    first = fetch_ocds_page(session, year=year, page=1, search=term)
                    pages = min(max_search_pages, int(first.get("pages", 1) or 1))
                    for p in range(1, pages + 1):
                        data = first if p == 1 else fetch_ocds_page(session, year=year, page=p, search=term)
                        for item in data.get("data", []):
                            ocid = (item.get("ocid") or "").strip()
                            if not ocid:
                                continue
                            rows.append(
                                {
                                    "year_query": year,
                                    "query_type": "thematic",
                                    "query_supplier_ruc": "",
                                    "ocid": ocid,
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
                                    "description": item.get("description"),
                                    "budget": item.get("budget"),
                                }
                            )
                        time.sleep(0.03)
                    detail[str(year)]["thematic_queries"] += 1
                except requests.RequestException:
                    continue

    # Historial por proveedores sancionados (más relevante para fraude)
    unique_rucs = sorted({r for r in sancion_rucs if re.fullmatch(r"\d{13}", r)})
    if enable_supplier_queries:
        for year in range(year_start, year_end + 1):
            for ruc in unique_rucs:
                try:
                    first = fetch_ocds_page(session, year=year, page=1, supplier=ruc)
                    pages = min(max_supplier_pages, int(first.get("pages", 1) or 1))
                    for p in range(1, pages + 1):
                        data = first if p == 1 else fetch_ocds_page(session, year=year, page=p, supplier=ruc)
                        for item in data.get("data", []):
                            ocid = (item.get("ocid") or "").strip()
                            if not ocid:
                                continue
                            rows.append(
                                {
                                    "year_query": year,
                                    "query_type": "supplier",
                                    "query_supplier_ruc": ruc,
                                    "ocid": ocid,
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
                                    "description": item.get("description"),
                                    "budget": item.get("budget"),
                                }
                            )
                        time.sleep(0.05)
                    detail[str(year)]["supplier_queries"] = detail[str(year)].get("supplier_queries", 0) + 1
                except requests.RequestException:
                    continue

    # Dedupe por combinación query+ocid para no perder relación proveedor
    dedup: list[dict[str, Any]] = []
    seen = set()
    for r in rows:
        key = (r.get("query_type"), r.get("query_supplier_ruc"), r.get("ocid"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)

    row_count = write_csv(
        output_csv,
        dedup,
        [
            "year_query",
            "query_type",
            "query_supplier_ruc",
            "ocid",
            "id",
            "year",
            "month",
            "method",
            "internal_type",
            "locality",
            "region",
            "suppliers",
            "buyer",
            "amount",
            "date",
            "title",
            "description",
            "budget",
        ],
    )
    return {
        "output_csv": str(output_csv.relative_to(ROOT)),
        "rows": row_count,
        "years": detail,
        "supplier_rucs_queried": len(unique_rucs),
    }


def build_inventory_manifest(
    year_start: int,
    year_end: int,
    ecu911_info: dict[str, Any],
    inec_info: dict[str, Any],
    sercop_info: dict[str, Any],
    ocds_info: dict[str, Any],
    ant_packages: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "year_start": year_start,
        "year_end": year_end,
        "confirmed_block": ["ckan", "inec", "sercop_ocds"],
        "sources": {
            "ckan_ecu911": ecu911_info,
            "ckan_ant_packages": ant_packages,
            "inec": inec_info,
            "sercop_sanciones": sercop_info,
            "ocds": ocds_info,
        },
        "static_sources": [
            {
                "id": s.id,
                "provider": s.provider,
                "temporal": f"{s.temporal_start}-{s.temporal_end}",
                "endpoints": [{"name": e.name, "url": e.url, "method": e.method} for e in s.endpoints],
                "maps_to": list(s.maps_to_tables),
            }
            for s in CONFIRMED_SOURCES
        ],
    }


def write_inventory_links(manifest: dict[str, Any], path: Path) -> None:
    lines = ["source\tcategory\turl\tmethod\tnote\n"]
    for src in manifest.get("static_sources", []):
        for ep in src.get("endpoints", []):
            lines.append(f"{src['id']}\t{src['provider']}\t{ep['url']}\t{ep['method']}\t\n")

    for res in manifest.get("sources", {}).get("ckan_ecu911", {}).get("resources_in_range", []):
        lines.append(
            f"ckan_ecu911\tECU911\t{res.get('url','')}\tdownload\t{res.get('name','')}\n"
        )

    for page_key, page in manifest.get("sources", {}).get("inec", {}).get("pages", {}).items():
        if isinstance(page, dict):
            lines.append(f"inec\tINEC\t{page.get('page','')}\thtml_scrape\t{page_key}\n")

    for year, payload in manifest.get("sources", {}).get("sercop_sanciones", {}).get("yearly", {}).items():
        if payload.get("url"):
            lines.append(f"sercop_sanciones\tSERCOP\t{payload['url']}\thtml_scrape\t{year}\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def write_data_dictionary(path: Path, year_start: int, year_end: int) -> int:
    rows = [
        {
            "dataset": f"ecu911_{year_start}_{year_end}.csv",
            "column": "source_file",
            "type": "string",
            "description": "Nombre del recurso original de ECU911",
            "map_to_reto": "siniestros",
        },
        {
            "dataset": f"inec_siniestros_{year_start}_{year_end}.csv",
            "column": "record_type",
            "type": "string",
            "description": "Tipo de registro extraído (table_cell o download_link)",
            "map_to_reto": "siniestros (contexto agregado)",
        },
        {
            "dataset": f"sercop_sanciones_{year_start}_{year_end}.csv",
            "column": "ruc",
            "type": "string(13)",
            "description": "RUC de proveedor sancionado cuando está disponible",
            "map_to_reto": "proveedores",
        },
        {
            "dataset": f"sercop_sanciones_{year_start}_{year_end}.csv",
            "column": "fecha_emision",
            "type": "date",
            "description": "Fecha de emisión de sanción detectada en texto",
            "map_to_reto": "proveedores",
        },
        {
            "dataset": f"ocds_proveedores_{year_start}_{year_end}.csv",
            "column": "ocid",
            "type": "string",
            "description": "Identificador OCDS del proceso de contratación",
            "map_to_reto": "proveedores",
        },
        {
            "dataset": f"ocds_proveedores_{year_start}_{year_end}.csv",
            "column": "query_supplier_ruc",
            "type": "string(13)",
            "description": "RUC usado en consulta supplier para traer historial",
            "map_to_reto": "proveedores",
        },
        {
            "dataset": f"ocds_proveedores_{year_start}_{year_end}.csv",
            "column": "amount",
            "type": "numeric_string",
            "description": "Monto adjudicado o asociado al proceso (si existe)",
            "map_to_reto": "proveedores",
        },
    ]
    return write_csv(path, rows, ["dataset", "column", "type", "description", "map_to_reto"])


def build_qa_report(
    year_start: int,
    year_end: int,
    ecu911_csv: Path,
    inec_csv: Path,
    sercop_csv: Path,
    ocds_csv: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    qa: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {"start": year_start, "end": year_end},
        "files": {},
        "checks": {},
    }
    for p in (ecu911_csv, inec_csv, sercop_csv, ocds_csv):
        qa["files"][str(p.relative_to(ROOT))] = {
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
        }

    # Check RUC saneado en SERCOP/OCDS
    ruc_valid = 0
    ruc_total = 0
    if sercop_csv.exists():
        with sercop_csv.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                ruc = (row.get("ruc") or "").strip()
                if ruc:
                    ruc_total += 1
                    if re.fullmatch(r"\d{13}", ruc):
                        ruc_valid += 1
    qa["checks"]["sercop_ruc_valid_ratio"] = (ruc_valid / ruc_total) if ruc_total else 0

    # Fechas parseables en SERCOP y OCDS
    def _parse_ok(value: str) -> bool:
        if not value:
            return False
        try:
            if "T" in value:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    fecha_ok = 0
    fecha_total = 0
    if sercop_csv.exists():
        with sercop_csv.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                v = row.get("fecha_emision", "")
                if v:
                    fecha_total += 1
                    if _parse_ok(v):
                        fecha_ok += 1
    if ocds_csv.exists():
        with ocds_csv.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                v = row.get("date", "")
                if v:
                    fecha_total += 1
                    if _parse_ok(v):
                        fecha_ok += 1
    qa["checks"]["fechas_parseables_ratio"] = (fecha_ok / fecha_total) if fecha_total else 0

    qa["checks"]["coverage_summary"] = {
        "ecu911_rows_by_year": manifest.get("sources", {}).get("ckan_ecu911", {}).get("rows_by_year", {}),
        "sercop_years": list((manifest.get("sources", {}).get("sercop_sanciones", {}).get("yearly", {}) or {}).keys()),
        "ocds_years": list((manifest.get("sources", {}).get("ocds", {}).get("years", {}) or {}).keys()),
    }
    return qa


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scraping completo Ecuador a CSV")
    p.add_argument("--year-start", type=int, default=DEFAULT_YEAR_START)
    p.add_argument("--year-end", type=int, default=DEFAULT_YEAR_END)
    p.add_argument("--ocds-max-supplier-pages", type=int, default=20)
    p.add_argument("--ocds-max-search-pages", type=int, default=20)
    p.add_argument("--ocds-disable-supplier-queries", action="store_true")
    p.add_argument("--ocds-disable-thematic-queries", action="store_true")
    p.add_argument("--skip-ecu911", action="store_true")
    p.add_argument("--skip-inec", action="store_true")
    p.add_argument("--skip-sercop", action="store_true")
    p.add_argument("--skip-ocds", action="store_true")
    p.add_argument("--reuse-existing", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    ecu911_csv = RAW_DIR / f"ecu911_{args.year_start}_{args.year_end}.csv"
    inec_csv = RAW_DIR / f"inec_siniestros_{args.year_start}_{args.year_end}.csv"
    sercop_csv = RAW_DIR / f"sercop_sanciones_{args.year_start}_{args.year_end}.csv"
    ocds_csv = RAW_DIR / f"ocds_proveedores_{args.year_start}_{args.year_end}.csv"

    session = _session()

    if args.reuse_existing and ecu911_csv.exists():
        ecu911_info = {"output_csv": str(ecu911_csv.relative_to(ROOT)), "reused_existing": True}
    elif args.skip_ecu911:
        ecu911_info = {"skipped": True}
    else:
        logger.info("Extrayendo ECU911...")
        ecu911_info = extract_ecu911(session, args.year_start, args.year_end, ecu911_csv)

    if args.reuse_existing and inec_csv.exists():
        inec_info = {"output_csv": str(inec_csv.relative_to(ROOT)), "reused_existing": True}
    elif args.skip_inec:
        inec_info = {"skipped": True}
    else:
        logger.info("Extrayendo INEC...")
        inec_info = extract_inec(session, inec_csv)

    if args.reuse_existing and sercop_csv.exists():
        sercop_info = {"output_csv": str(sercop_csv.relative_to(ROOT)), "reused_existing": True, "unique_rucs": []}
    elif args.skip_sercop:
        sercop_info = {"skipped": True, "unique_rucs": []}
    else:
        logger.info("Extrayendo SERCOP...")
        sercop_info = extract_sercop(session, args.year_start, args.year_end, sercop_csv)
    sancion_rucs = sercop_info.get("unique_rucs", [])

    if args.reuse_existing and ocds_csv.exists():
        ocds_info = {"output_csv": str(ocds_csv.relative_to(ROOT)), "reused_existing": True}
    elif args.skip_ocds:
        ocds_info = {"skipped": True}
    else:
        logger.info("Extrayendo OCDS (orientado a proveedores)...")
        ocds_info = extract_ocds(
            session,
            args.year_start,
            args.year_end,
            sancion_rucs=sancion_rucs,
            output_csv=ocds_csv,
            max_supplier_pages=args.ocds_max_supplier_pages,
            max_search_pages=args.ocds_max_search_pages,
            enable_supplier_queries=not args.ocds_disable_supplier_queries,
            enable_thematic_queries=not args.ocds_disable_thematic_queries,
        )

    try:
        ant_packages = fetch_ckan_organization_packages(session, "antec")
    except requests.RequestException as exc:
        ant_packages = [{"error": str(exc)}]

    manifest = build_inventory_manifest(
        args.year_start, args.year_end, ecu911_info, inec_info, sercop_info, ocds_info, ant_packages
    )

    manifest_path = MANIFEST_DIR / "inventario_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    links_path = MANIFEST_DIR / "inventario_links.tsv"
    write_inventory_links(manifest, links_path)

    dictionary_path = MANIFEST_DIR / "data_dictionary_ecuador.csv"
    write_data_dictionary(dictionary_path, args.year_start, args.year_end)

    qa = build_qa_report(
        args.year_start, args.year_end, ecu911_csv, inec_csv, sercop_csv, ocds_csv, manifest
    )
    qa_path = MANIFEST_DIR / "qa_report.json"
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"CSV ECU911:    {ecu911_csv}")
    print(f"CSV INEC:      {inec_csv}")
    print(f"CSV SERCOP:    {sercop_csv}")
    print(f"CSV OCDS:      {ocds_csv}")
    print(f"Manifiesto:    {manifest_path}")
    print(f"Links:         {links_path}")
    print(f"Diccionario:   {dictionary_path}")
    print(f"QA:            {qa_path}")


if __name__ == "__main__":
    main()
