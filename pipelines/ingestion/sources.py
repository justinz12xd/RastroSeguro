"""
Fuentes oficiales de Ecuador para enriquecimiento de siniestros (hackIAthon).

Bloque inicial confirmado: CKAN (datosabiertos.gob.ec) + INEC + SERCOP/OCDS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SourceKind = Literal["api", "download", "html_scrape", "hybrid"]


@dataclass(frozen=True)
class SourceEndpoint:
    """Un endpoint o página descargable asociada a una fuente."""

    name: str
    url: str
    method: SourceKind
    description: str = ""
    notes: str = ""


@dataclass(frozen=True)
class EcuadorSource:
    """Metadatos de una fuente pública ecuatoriana."""

    id: str
    provider: str
    category: str
    temporal_start: int
    temporal_end: int
    license_note: str
    endpoints: tuple[SourceEndpoint, ...] = field(default_factory=tuple)
    fields_available: tuple[str, ...] = field(default_factory=tuple)
    maps_to_tables: tuple[str, ...] = field(default_factory=tuple)


# Periodo por defecto alineado con disponibilidad pública reciente (ECU911 mensual ~2021+).
DEFAULT_YEAR_START = 2021
DEFAULT_YEAR_END = 2026

CONFIRMED_SOURCES: tuple[EcuadorSource, ...] = (
    EcuadorSource(
        id="ckan_ecu911",
        provider="Datos Abiertos Ecuador / ECU 911",
        category="emergencias_incidentes",
        temporal_start=2021,
        temporal_end=DEFAULT_YEAR_END,
        license_note="Creative Commons Attribution (cc-by) en catálogo ECU911",
        endpoints=(
            SourceEndpoint(
                name="package_show",
                url="https://www.datosabiertos.gob.ec/api/3/action/package_show",
                method="api",
                description="Metadatos y lista de recursos CSV/XLSX mensuales",
                notes="Query: id=base-de-emergencias",
            ),
            SourceEndpoint(
                name="dataset_page",
                url="https://www.datosabiertos.gob.ec/dataset/base-de-emergencias",
                method="hybrid",
                description="Página humana + enlaces de descarga directa",
            ),
        ),
        fields_available=(
            "fecha_emergencia",
            "tipo_emergencia",
            "provincia",
            "canton",
            "parroquia",
            "coordenadas_aprox",
            "institucion_atencion",
        ),
        maps_to_tables=("siniestros",),
    ),
    EcuadorSource(
        id="ckan_ant",
        provider="Datos Abiertos Ecuador / ANT",
        category="transito_vehiculos",
        temporal_start=2020,
        temporal_end=DEFAULT_YEAR_END,
        license_note="Ver licencia por dataset en CKAN",
        endpoints=(
            SourceEndpoint(
                name="organization_datasets",
                url="https://datosabiertos.gob.ec/dataset/?organization=antec",
                method="html_scrape",
                description="Catálogo ANT (excesos velocidad, transporte)",
            ),
            SourceEndpoint(
                name="package_search",
                url="https://www.datosabiertos.gob.ec/api/3/action/package_search",
                method="api",
                notes="Query: fq=organization:antec",
            ),
        ),
        fields_available=("placa_kit", "velocidad", "ruta", "fecha_registro"),
        maps_to_tables=("vehiculos", "siniestros"),
    ),
    EcuadorSource(
        id="ckan_transport_csv",
        provider="Datos Abiertos Ecuador",
        category="transporte_general",
        temporal_start=2020,
        temporal_end=DEFAULT_YEAR_END,
        license_note="Filtrar res_format=CSV en catálogo",
        endpoints=(
            SourceEndpoint(
                name="csv_catalog",
                url="https://www.datosabiertos.gob.ec/dataset/?res_format=CSV&groups=trans",
                method="html_scrape",
            ),
            SourceEndpoint(
                name="sri_vehiculos",
                url="https://www.datosabiertos.gob.ec/dataset/estadisticas-vehiculos-2024",
                method="hybrid",
                description="Marca, modelo, año, cantón (ventas vehículos)",
            ),
        ),
        fields_available=("marca", "modelo", "anio", "canton", "clase_vehiculo"),
        maps_to_tables=("vehiculos", "polizas"),
    ),
    EcuadorSource(
        id="inec_siniestros",
        provider="INEC / ESTRA (fuente ANT)",
        category="estadisticas_agregadas",
        temporal_start=2014,
        temporal_end=DEFAULT_YEAR_END,
        license_note="CC BY 4.0 Internacional",
        endpoints=(
            SourceEndpoint(
                name="anual",
                url="https://www.ecuadorencifras.gob.ec/estadisticas-siniestros-de-transito/",
                method="html_scrape",
            ),
            SourceEndpoint(
                name="trimestral",
                url="https://www.ecuadorencifras.gob.ec/siniestros-transito-trimestral/",
                method="html_scrape",
            ),
            SourceEndpoint(
                name="bases_datos",
                url="https://www.ecuadorencifras.gob.ec/estadistica-de-transporte-bases-de-datos/",
                method="html_scrape",
                description="Enlaces SPSS/CSV vehículos matriculados",
            ),
        ),
        fields_available=(
            "num_siniestros",
            "lesionados",
            "fallecidos",
            "provincia",
            "trimestre",
            "tipo_vehiculo",
            "causa",
        ),
        maps_to_tables=("siniestros",),
    ),
    EcuadorSource(
        id="sercop_sanciones",
        provider="SERCOP",
        category="proveedores_lista_restrictiva",
        temporal_start=2020,
        temporal_end=DEFAULT_YEAR_END,
        license_note="Resoluciones públicas; extraer RUC y estado vigente",
        endpoints=(
            SourceEndpoint(
                name="sanciones_2024",
                url="https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones2024",
                method="html_scrape",
            ),
            SourceEndpoint(
                name="sanciones_2023",
                url="https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones-2023",
                method="html_scrape",
            ),
            SourceEndpoint(
                name="sanciones_2020",
                url="https://portal.compraspublicas.gob.ec/sercop/cat_normativas/Sanciones-2020",
                method="html_scrape",
            ),
        ),
        fields_available=(
            "razon_social",
            "ruc",
            "motivo",
            "fecha_emision",
            "estado",
            "plazo_suspension_dias",
        ),
        maps_to_tables=("proveedores",),
    ),
    EcuadorSource(
        id="ocds_contratacion",
        provider="Contrataciones Abiertas Ecuador / SERCOP",
        category="proveedores_historial",
        temporal_start=2020,
        temporal_end=DEFAULT_YEAR_END,
        license_note="CC BY 3.0 EC; actualización diaria",
        endpoints=(
            SourceEndpoint(
                name="search_ocds",
                url="https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/search_ocds",
                method="api",
                notes="Params: year, search, page, buyer, supplier",
            ),
            SourceEndpoint(
                name="record_ocds",
                url="https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/api/record",
                method="api",
                notes="Param: ocid",
            ),
            SourceEndpoint(
                name="api_docs",
                url="https://datosabiertos.compraspublicas.gob.ec/PLATAFORMA/datos-abiertos/api",
                method="download",
            ),
        ),
        fields_available=(
            "ocid",
            "buyer_name",
            "supplier_name",
            "supplier_id",
            "award_amount",
            "procedure_type",
        ),
        maps_to_tables=("proveedores",),
    ),
    EcuadorSource(
        id="gob_ec_tramites",
        provider="Gob.ec / ANT / CTE",
        category="tramites_referencia",
        temporal_start=DEFAULT_YEAR_START,
        temporal_end=DEFAULT_YEAR_END,
        license_note="Solo metadatos de trámite; no datos masivos por placa",
        endpoints=(
            SourceEndpoint(
                name="cte_estadisticas",
                url="https://www.gob.ec/cte/tramites/provision-estadisticas-siniestros-transito",
                method="download",
                description="Solicitud formal para estadísticas agregadas CTE",
            ),
            SourceEndpoint(
                name="ant_taller",
                url="https://www.gob.ec/ant/tramites/exoneracion-multas-calendarizacion-vehiculo-se-encuentra-taller-mecanico-no-se-presenta-revision-tecnica-vehicular",
                method="download",
            ),
        ),
        fields_available=(),
        maps_to_tables=(),
    ),
)

SOURCE_BY_ID = {s.id: s for s in CONFIRMED_SOURCES}
