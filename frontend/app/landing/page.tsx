import type { Metadata } from 'next'
import { LandingPageContent } from '@/components/landing/landing-page-content'

export const metadata: Metadata = {
  title: 'RastroSeguro | Inteligencia antifraude',
  description:
    'RastroSeguro prioriza siniestros con señales de posible fraude y explica por qué, para que el equipo humano revise primero donde más importa.',
}

export default function LandingPage() {
  return <LandingPageContent />
}
