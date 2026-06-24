# Entregables — hackIAthon 2026

Carpeta de entrega oficial del equipo **RastroSeguro** (Reto Aseguradora del Sur).

| # | Entregable | Carpeta |
|---|------------|---------|
| 1 | Prototipo funcional (Dashboard / API / notebooks) | [`01-prototipo-funcional/`](./01-prototipo-funcional/) |
| 2 | Código fuente + README detallado | [`02-codigo-fuente/`](./02-codigo-fuente/) |
| 3 | Dataset sintético y datos públicos | [`03-dataset/`](./03-dataset/) |
| 4 | Presentación ejecutiva (PDF) | [`04-presentacion-ejecutiva/`](./04-presentacion-ejecutiva/) |

## Demo rápida

```bash
# Desde la raíz del repositorio
uvicorn api.main:app --reload --port 8000
cd frontend && npm run dev
```

Abrir http://localhost:3000 → **Entrar a la plataforma**.

## Validación

```bash
py -3 -m pipelines.models.validate_deliverables
```

## Equipo

Carlos (datos/modelos) · Jeremy (scoring/agente) · Justin (dashboard/demo)
