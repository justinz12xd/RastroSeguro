'use client'

import dynamic from 'next/dynamic'
import { Map, ShieldAlert } from 'lucide-react'
import type { MapLocation } from '@/components/ecuador-leaflet-map'

type CityKey = 'Quito' | 'Guayaquil' | 'Cuenca' | 'Manta'

const CITY_META: Record<CityKey, { provincia: string; lat: number; lng: number; altaSiniestralidad: boolean }> = {
  Quito: { provincia: 'Pichincha', lat: -0.1807, lng: -78.4678, altaSiniestralidad: true },
  Guayaquil: { provincia: 'Guayas', lat: -2.1894, lng: -79.8891, altaSiniestralidad: true },
  Cuenca: { provincia: 'Azuay', lat: -2.9001, lng: -79.0059, altaSiniestralidad: false },
  Manta: { provincia: 'Manabí', lat: -0.9677, lng: -80.7089, altaSiniestralidad: false },
}

const EcuadorLeafletMap = dynamic(
  () => import('@/components/ecuador-leaflet-map').then((m) => m.EcuadorLeafletMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[min(320px,42vw)] min-h-[240px] w-full items-center justify-center bg-[var(--surface-container)]">
        <p className="text-sm text-muted-foreground">Cargando mapa…</p>
      </div>
    ),
  },
)

function resolveMeta(ciudad?: string | null) {
  const key = (ciudad || '').trim() as CityKey
  const found = CITY_META[key]
  if (found) {
    return {
      ciudad: key,
      provincia: found.provincia,
      lat: found.lat.toFixed(4),
      lng: found.lng.toFixed(4),
      altaSiniestralidad: found.altaSiniestralidad,
      mapLocation: { ciudad: key, lat: found.lat, lng: found.lng } satisfies MapLocation,
    }
  }
  return {
    ciudad: key || 'Ubicación no informada',
    provincia: 'Ecuador',
    lat: '—',
    lng: '—',
    altaSiniestralidad: false,
    mapLocation: { ciudad: key || 'Ecuador', lat: -1.8312, lng: -78.1834 } satisfies MapLocation,
  }
}

export function GeographicContextCard({ ciudad }: { ciudad?: string | null }) {
  const meta = resolveMeta(ciudad)

  return (
    <div className="institutional-card overflow-hidden">
      <div className="section-header flex items-center justify-between gap-2">
        <span className="flex items-center gap-2">
          <Map className="h-4 w-4 shrink-0" aria-hidden />
          Contexto geográfico
        </span>
        {meta.altaSiniestralidad && (
          <span className="inline-flex items-center gap-1 rounded-sm bg-[var(--warning-container)] px-2 py-0.5 text-xs font-semibold text-[var(--on-warning-container)]">
            <ShieldAlert className="h-3 w-3" aria-hidden />
            Zona observada
          </span>
        )}
      </div>

      <EcuadorLeafletMap location={meta.mapLocation} />

      <div className="grid grid-cols-2 divide-x divide-border border-t border-border bg-[var(--surface-lowest)]">
        <div className="p-4">
          <p className="label-mono text-muted-foreground">Ciudad</p>
          <p className="mt-1 font-display text-lg font-bold text-foreground">{meta.ciudad}</p>
        </div>
        <div className="p-4">
          <p className="label-mono text-muted-foreground">Provincia</p>
          <p className="mt-1 text-sm font-semibold text-foreground">{meta.provincia}</p>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border bg-[var(--surface-low)] px-4 py-3">
        <div className="flex items-center gap-2 text-sm">
          <span className="label-mono text-muted-foreground">LAT</span>
          <span className="font-mono text-foreground">{meta.lat}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="label-mono text-muted-foreground">LNG</span>
          <span className="font-mono text-foreground">{meta.lng}</span>
        </div>
      </div>
    </div>
  )
}
