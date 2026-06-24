"""Intent definitions for the tool-backed antifraud agent."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentMatch:
    name: str
    confidence: float
    requires_claim_id: bool = False
    uses_documentation: bool = False


INTENT_ALIASES = {
    "fecha_actual": [
        "que dia es hoy",
        "qué día es hoy",
        "que fecha es hoy",
        "qué fecha es hoy",
        "fecha de hoy",
        "fecha actual",
        "dia de hoy",
        "día de hoy",
        "en que fecha estamos",
        "en qué fecha estamos",
    ],
    "saludo": ["hola", "buenas", "buenos dias", "buenos días", "buenas tardes", "buenas noches"],
    "ayuda_agente": [
        "ayuda",
        "que puedes hacer",
        "qué puedes hacer",
        "que puedo preguntar",
        "qué puedo preguntar",
        "opciones",
        "comandos",
        "preguntas sugeridas",
    ],
    "top_riesgo": ["top", "mayor riesgo", "mas riesgo", "más riesgo", "prioridad", "priorizar", "mas riesgosos", "más riesgosos", "peores casos", "ranking de riesgo", "10 siniestros", "diez siniestros", "casos sospechosos"],
    "explicar_siniestro": ["explica", "explicame", "explícame", "por que", "por qué", "detalle", "porque", "por que este", "por qué este", "marcado como alto", "por que es riesgoso", "razones", "motivo", "justifica", "fundamenta", "por que fue marcado"],
    "expediente_siniestro": ["expediente", "ficha antifraude", "dossier", "investigacion", "investigación", "ficha del caso", "ficha completa"],
    "ranking_proveedores": ["proveedor", "proveedores", "taller", "talleres", "clinica", "clínica", "concentran", "alertas rojas", "intermediario", "intermediarios", "que proveedores"],
    "ranking_ciudades": ["ciudad", "ciudades", "zona", "concentracion", "concentración", "geografico", "geográfico", "provincia", "que ciudades"],
    "riesgo_por_ramo": ["ramo", "ramos", "multi ramo", "multiramo", "sospechosos", "porcentaje", "por ramo", "tipo de seguro", "linea de negocio", "línea de negocio", "que ramos"],
    "documentos_faltantes": ["documento", "documentos", "faltan", "incompletos", "criticos", "críticos", "papeles", "soportes faltantes", "falta documentacion"],
    "narrativas_similares": ["narrativa", "narrativas", "relato", "relatos", "similares", "clonada", "clonadas", "similitud", "parecidas", "narrativas parecidas", "relatos iguales"],
    "conexiones_grafo": [
        "grafo",
        "conexion",
        "conexión",
        "conexiones",
        "relacion del caso",
        "relación del caso",
        "relaciones del",
        "conexiones del siniestro",
        "vinculo",
        "vínculo",
        "vinculos",
        "vínculos",
        "entidades recurrentes",
        "esta conectado",
        "está conectado",
        "red del caso",
    ],
    "redes_fraude": [
        "red de fraude",
        "redes de fraude",
        "anillo",
        "anillos",
        "ring",
        "rings",
        "organizado",
        "organizados",
        "banda",
        "redes organizadas",
        "fraude organizado",
        "coordinacion",
        "coordinación",
    ],
    "resumen_ejecutivo": ["resumen", "ejecutivo", "gerencia", "casos criticos", "casos críticos", "resumen gerencial", "panorama", "vision general", "visión general"],
    "casos_estrella": ["casos estrella", "demo ejecutiva", "casos demo", "caso rojo evidente", "rojo no evidente"],
    "impacto_negocio": ["impacto", "negocio", "exposicion", "exposición", "top 10%", "cuanto se expone", "exposicion del portafolio"],
    "recomendar_revision": ["recomienda", "revisar primero", "orden de revision", "orden de revisión", "deberia revisar", "debería revisar", "que reviso primero", "por donde empiezo", "cola de revision", "prioridad de revision"],
    "frecuencia_asegurados": ["asegurados", "frecuencia de reclamos", "mas reclamos", "más reclamos", "que asegurados", "reclaman mas", "reclaman más", "reincidentes", "clientes recurrentes"],
    "montos_atipicos": ["montos atipicos", "montos atípicos", "monto atipico", "monto atípico", "monto inusual", "montos inusuales", "inusual", "montos altos", "sobrevaluado", "valores atipicos", "monto fuera de lo normal"],
    "borde_vigencia": ["cerca del inicio", "inicio de la poliza", "inicio de la póliza", "borde de vigencia", "recien contratada", "recién contratada", "apenas firmada", "cerca de la vigencia"],
    "patrones_repetidos": ["patrones", "patron", "patrón", "se repiten", "repetidos", "patrones comunes", "que se repite", "comportamientos repetidos"],
    "simular_siniestro": ["simula", "simular", "simulación", "simulacion", "nuevo siniestro"],
    "ahorro_potencial": ["ahorro", "ahorros", "perdida evitada", "pérdida evitada", "savings", "potencial"],
    "concentracion_rojos": ["80%", "80 por ciento", "ochenta por ciento", "concentran el 80", "alertas rojas proveedores"],
    "documentacion": ["regla", "reglas", "score", "metodologia", "metodología", "limitacion", "limitación", "etica", "ética", "documentacion", "documentación", "como funciona", "cómo funciona", "como calculan", "cómo calculan", "como se calcula", "cómo se calcula", "que reglas", "qué reglas", "explica el sistema", "como detectan el fraude"],
}

GENERAL_INTENTS = {"fecha_actual", "saludo", "ayuda_agente"}
CLAIM_REQUIRED_INTENTS = {"explicar_siniestro", "expediente_siniestro", "narrativas_similares", "conexiones_grafo"}
DOC_INTENTS = {"documentacion"}
