# RastroSeguro — Pitch ejecutivo (hackIAthon 2026)

**Reto Aseguradora del Sur — Detector de posibles fraudes en siniestros con IA**

Equipo: Carlos (datos/modelos), Jeremy (scoring/agente), Justin (dashboard/demo)

---

## 1. Problema y oportunidad (1 min)

Las aseguradoras procesan miles de siniestros con señales dispersas: fechas atípicas, proveedores recurrentes, documentos inconsistentes, narrativas repetidas. La revisión manual es lenta y depende de la experiencia del analista.

**Oportunidad:** priorizar casos sospechosos con IA explicable antes de escalar a antifraude, reduciendo pérdidas y mejorando el control operativo.

---

## 2. Solución propuesta (1 min)

**RastroSeguro** es un prototipo híbrido que:

- Calcula un **score de riesgo 0–100** por siniestro
- Clasifica en semáforo **Verde / Amarillo / Rojo**
- Activa **reglas auditables** (RF-01…RF-07 del PDF)
- Combina **ML + anomalías + NLP + grafo de relaciones**
- Ofrece un **agente** con consultas en lenguaje natural
- **No acusa fraude** ni rechaza pagos — genera alertas para revisión humana

---

## 3. Demo funcional (4 min)

### Flujo en vivo

1. **Command Center:** panorama de casos rojos, proveedores y ahorro potencial estimado
2. **Análisis de caso:** score desglosado, `rule_trace`, explicación textual
3. **Agente IA:** *"¿Qué proveedores concentran el 80% de las alertas rojas?"*
4. **Simulador:** siniestro 24 h después de la póliza → RF-05 Amarillo/Rojo con explicación
5. **Reporte auditoría:** export Markdown con top casos y reglas activadas

### Comandos

```bash
uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev
```

---

## 4. Arquitectura y uso de IA (2 min)

```txt
Datos sintéticos → Features → Reglas + ML + Anomalías + NLP + Grafo
    → Score final → Dashboard + API + Agente + Reportes
```

| Componente | Tecnología | Peso |
|------------|------------|------|
| Reglas RF/RB/RV | Python determinístico | 30% |
| Clasificador | RandomForest | 25% |
| Anomalías | IsolationForest | 15% |
| NLP narrativas | TF-IDF + coseno | 15% |
| Grafo | Recurrencia entidades | 10% |
| Perfil categórico | Por ramo | 5% |

**Stack:** Python, FastAPI, Next.js, Postgres/Supabase, Oracle XE (referencia), R (validación).

Documentación: `docs/arquitectura.md`, `docs/uso_ia.md`, `docs/reglas_negocio.md`

---

## 5. Impacto de negocio (1 min)

- **Analista de siniestros:** bandeja priorizada con explicación de alertas
- **Antifraude:** detección temprana de patrones (proveedor recurrente, borde vigencia, narrativa clonada)
- **Gerencia:** estimación de ahorro potencial por revisión temprana de casos rojos
- **Auditoría:** trazabilidad completa (`rule_trace`, reportes exportables)

Escalabilidad: esquemas SQL (Postgres/Oracle), API REST, pipeline reproducible.

---

## 6. Limitaciones y próximos pasos (1 min)

### Limitaciones

- Datos 100% sintéticos; métricas altas no garantizan producción
- LLM opcional; demo funciona sin API externa
- Estimación de ahorro es ilustrativa, no garantizada

### Próximos pasos

1. Integración con core de pólizas/siniestros de la aseguradora
2. Calibración con datos reales anonimizados
3. Despliegue en Oracle/Postgres con monitoreo de drift
4. Feedback loop del analista para reducir falsos positivos

---

## Preguntas frecuentes del jurado

**¿Cómo detectan similitud narrativa?**  
TF-IDF + similitud coseno; ≥85% → 8 pts, 70–84% → 4 pts (PDF §7).

**¿Cómo evitan acusar injustamente?**  
Lenguaje de "posible fraude / requiere revisión"; sin rechazo automático; documentado en `docs/limitaciones.md`.

**¿Cómo ayuda al analista?**  
Top 10 casos, explicación por regla, agente NL, simulador what-if, reporte auditoría.

---

*RastroSeguro — hackIAthon 2026 — Aseguradora del Sur*
