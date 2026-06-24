# 1. Prototipo funcional

## Componentes

| Componente | Ruta en el repo | Descripción |
|------------|-----------------|-------------|
| Dashboard | `frontend/` | Next.js — landing, command center, análisis de casos, agente IA |
| API REST | `api/` | FastAPI — claims, scoring, agente, reportes, health |
| Notebooks | `notebooks/` | Exploración, entrenamiento y evaluación del modelo |

## Cómo ejecutar

### Requisitos

- Python 3.11+
- Node.js 18+

### Instalación (una vez)

```bash
pip install -r requirements.txt
cd frontend && npm install
```

### Pipeline de datos (una vez)

```bash
py -3 -m pipelines.models.run_carlos_pipeline --rows 25000 --seed 42 --scoring-rows 2000
```

### Levantar demo

Terminal A:

```bash
uvicorn api.main:app --reload --port 8000
```

Terminal B:

```bash
cd frontend
npm run dev
```

### Notebooks (alternativa)

```bash
jupyter notebook notebooks/01_exploracion_datos.ipynb
```

## Flujo demo sugerido (~4 min)

1. Command Center — casos rojos y ahorro potencial
2. Análisis de caso — score, semáforo, reglas activadas
3. Agente IA — consultas en lenguaje natural
4. Simulador — siniestro 24 h post-póliza
5. Reporte de auditoría — export Markdown
