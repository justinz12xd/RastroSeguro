# RastroSeguro — App móvil (dashboard ejecutivo)

Dashboard administrativo en React Native (Expo) que consume el mismo FastAPI del frontend web.

## Requisitos

- Node.js 20+
- Backend RastroSeguro corriendo en `:8000`
- Expo Go en el celular **o** emulador Android/iOS

## Instalación

```bash
cd app-mobile
npm install
```

## Ejecutar

```bash
# Terminal 1 — API (desde la raíz del monorepo)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — app móvil
cd app-mobile
npm start
```

Luego escanea el QR con Expo Go, o pulsa `a` / `i` / `w` para Android / iOS / web.

## API URL

Por defecto:

| Plataforma | URL |
|------------|-----|
| iOS Simulator / web | `http://localhost:8000` |
| Emulador Android | `http://10.0.2.2:8000` |
| Dispositivo físico | IP LAN de tu PC |

Para dispositivo físico, copia `.env.example` → `.env` y ajusta:

```env
EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
```

El backend debe aceptar CORS desde el origen del cliente (o servir en red local). Arranca uvicorn con `--host 0.0.0.0`.

## Estilos

Tokens portados desde `frontend/app/globals.css` (indigo brand, semáforo, surfaces).
Tipografía: IBM Plex Sans + JetBrains Mono (mismas familias del web).

## Primera vista

Tabs: **Control** (dashboard) e **Impacto** (business impact + star cases).

- KPIs, pie de semáforo, barras (ramo / proveedor / ciudad) y top casos vía `GET /api/report`
- Tocar un caso abre el **expediente** (`GET /api/claims/{id}/dossier`)
- Impacto vía `GET /api/reports/business-impact` y `GET /api/reports/star-cases`

Gráficos con `react-native-gifted-charts` + `react-native-svg`, mismos colores del design system web.
