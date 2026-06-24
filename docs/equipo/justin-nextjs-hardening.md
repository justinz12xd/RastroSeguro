# Pendientes de Justin: hardening Next.js para demo

Justin, el frontend ya avanzó bastante: el chatbot se ve mejor, la integración con FastAPI compila y el upload ya quedó alineado a CSV. Antes de seguir agregando pantallas, conviene cerrar estos puntos para que la demo sea estable y no dependa de condiciones frágiles.

## Decisión rápida

Mantén lo último que subiste, pero haz un commit pequeño de hardening enfocado en estabilidad:

1. Restaurar modo demo sin obligar a subir CSV.
2. Terminar la decisión de usar solo Bun.
3. Corregir dependencias/runtime del upload CSV.
4. Hacer que build y typecheck sean honestos.
5. Alinear datos visibles a Ecuador.

## Estado validado por Jeremy

Último commit revisado:

```txt
cd3d37a Se elimina pnpm como manejador de paquetes, solo se usará bun
```

Checks ejecutados:

```bash
cd frontend
bun run build        # OK
bunx tsc --noEmit    # OK
bun run lint         # FALLA: eslint no está instalado

cd ..
uv run python -m unittest discover -s tests -v  # 59 tests OK
```

## Checklist prioritario

### P0: debe quedar antes de demo

| Pendiente | Archivo | Qué hacer | Por qué importa |
|---|---|---|---|
| Restaurar modo demo sin CSV | `frontend/components/steps/step-upload.tsx` | Volver a cargar casos existentes con `loadClaims()` al abrir la pantalla, o agregar botón “Usar dataset demo”. | Si el upload falla o no tenemos CSV a mano, la demo queda bloqueada. |
| Terminar “solo Bun” | `frontend/package-lock.json` | Si la decisión es Bun, eliminar `package-lock.json` y documentar comandos con Bun. | Ahora quedan `bun.lock` y `package-lock.json`; eso confunde al equipo. |
| Declarar multipart | `requirements.txt` | Añadir `python-multipart>=0.0.9`. | `UploadFile = File(...)` en FastAPI lo necesita en una instalación limpia. |
| Quitar build inseguro | `frontend/next.config.mjs` | Remover `typescript.ignoreBuildErrors = true`. | Ya `bunx tsc --noEmit` pasa; no ocultemos errores para la demo. |
| Arreglar lint | `frontend/package.json` | O instalar/configurar ESLint, o cambiar el script temporalmente. | Ahora `bun run lint` falla siempre. |

### P1: muy recomendado para que se vea coherente

| Pendiente | Archivo | Qué hacer | Por qué importa |
|---|---|---|---|
| Ecuadorizar mocks | `frontend/lib/claims-data.ts` | Cambiar Medellín/Bogotá/Cali/Barranquilla por Guayaquil/Quito/Cuenca/Manta, y `es-CO` por `es-EC`. | El reto y los datos de Carlos están orientados a Ecuador. |
| Mantener copy consistente | Varias vistas | Usar español institucional en todos los botones principales. | Hay mezcla de “Proceed”, “Risk Level”, “Upload Data”. |
| No sobrescribir demo principal al subir CSV | `api/routes/claims.py` + frontend | Ideal: guardar upload en salida temporal o avisar claramente que reemplaza el scoring activo. | Evita dañar `data/processed/siniestros_scored.csv` durante demo. |

## Flujo recomendado de la pantalla de upload

La pantalla debe soportar dos caminos:

### Camino A: demo rápida

1. Next llama `GET /api/health`.
2. Next llama `GET /api/claims?limit=50`.
3. Si hay casos, mostrar selector/lista “Usar dataset demo”.
4. Usuario elige un siniestro y avanza a resumen/análisis.

### Camino B: CSV nuevo

1. Usuario sube `.csv`.
2. Next llama `POST /api/claims/upload-csv`.
3. Backend regenera scoring.
4. Next vuelve a llamar `GET /api/claims?limit=50`.
5. Usuario elige un siniestro del CSV procesado.

## Comandos esperados si usamos Bun

```bash
cd frontend
bun install
bun run dev
bun run build
bunx tsc --noEmit
```

Si se arregla lint:

```bash
bun run lint
```

## Criterios de aceptación

Antes de avisar que quedó listo:

- [ ] `frontend/package-lock.json` ya no existe si seguimos con Bun.
- [ ] `frontend/bun.lock` queda como único lockfile del frontend.
- [ ] `bun run build` pasa.
- [ ] `bunx tsc --noEmit` pasa.
- [ ] `bun run lint` pasa o el script queda removido/documentado temporalmente.
- [ ] La pantalla de upload permite demo sin subir CSV.
- [ ] La pantalla de upload acepta solo `.csv`.
- [ ] `requirements.txt` incluye `python-multipart`.
- [ ] Los textos/datos visibles no contradicen Ecuador.

## Nota de coordinación

Justin no debe mover lógica antifraude a TypeScript. El frontend consume contratos del backend. Si necesita un dato nuevo para UI, pedirlo en `api/` y documentarlo en `docs/equipo/justin-nextjs-puente-api.md`.
