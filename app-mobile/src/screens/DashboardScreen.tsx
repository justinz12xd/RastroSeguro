import { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ApiClientError, getApiBaseUrl, getExecutiveReport, type ExecutiveReport } from '../lib/api'
import { formatCurrency, formatNumber, formatPercent } from '../lib/format'
import { colors, radius, spacing } from '../theme/tokens'
import { fonts, textStyles } from '../theme/typography'
import { KpiCard } from '../components/KpiCard'
import { RiskBarChart } from '../components/RiskBarChart'
import { RiskBadge } from '../components/RiskBadge'
import { SectionHeader } from '../components/SectionHeader'
import { SemaphorePieChart } from '../components/SemaphorePieChart'

export function DashboardScreen() {
  const [report, setReport] = useState<ExecutiveReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<{ message: string; hint?: string | null } | null>(null)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)
    try {
      const data = await getExecutiveReport(10)
      setReport(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido'
      const hint = err instanceof ApiClientError ? err.hint : null
      setError({ message, hint })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const summary = report?.summary

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'left', 'right']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => void load(true)}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      >
        <View style={styles.hero}>
          <Text style={styles.brand}>RastroSeguro</Text>
          <Text style={textStyles.display}>Centro de control</Text>
          <Text style={[textStyles.subtitle, styles.heroCopy]}>
            Panorama de riesgo, recurrencia e impacto — vista ejecutiva móvil.
          </Text>
          <Text style={styles.apiHint}>API · {getApiBaseUrl()}</Text>
        </View>

        {loading && !report ? (
          <View style={styles.centerState}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[textStyles.subtitle, styles.stateText]}>Cargando reporte ejecutivo…</Text>
          </View>
        ) : null}

        {error && !report ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>No se pudo cargar el dashboard</Text>
            <Text style={textStyles.body}>{error.message}</Text>
            {error.hint ? <Text style={[textStyles.subtitle, styles.stateText]}>{error.hint}</Text> : null}
            <Pressable style={styles.retryBtn} onPress={() => void load()}>
              <Text style={styles.retryText}>Reintentar</Text>
            </Pressable>
          </View>
        ) : null}

        {summary ? (
          <>
            <View style={styles.kpiGrid}>
              <KpiCard label="Siniestros" value={formatNumber(summary.total_siniestros)} />
              <KpiCard
                label="Casos rojos"
                value={formatNumber(summary.casos_rojos)}
                hint={formatPercent(summary.porcentaje_rojo)}
                accent="rojo"
              />
              <KpiCard
                label="Monto expuesto"
                value={formatCurrency(summary.monto_total_reclamado)}
              />
              <KpiCard
                label="Puntaje medio"
                value={String(Math.round(summary.score_promedio_portafolio ?? 0))}
                hint="Escala 0–100"
                accent="amarillo"
              />
            </View>

            {report?.ahorro_potencial_estimado ? (
              <View style={styles.savingsCard}>
                <Text style={[textStyles.labelMono, { color: colors.riskVerde }]}>
                  Ahorro potencial estimado
                </Text>
                <Text style={[textStyles.kpiValue, { color: colors.onSuccessContainer }]}>
                  {formatCurrency(report.ahorro_potencial_estimado.ahorro_potencial_estimado)}
                </Text>
                {report.ahorro_potencial_estimado.nota_etica ? (
                  <Text style={[textStyles.label, styles.savingsNote]}>
                    {report.ahorro_potencial_estimado.nota_etica}
                  </Text>
                ) : null}
              </View>
            ) : null}

            <View style={styles.section}>
              <SectionHeader
                title="Distribución por semáforo"
                subtitle="Mix crítico / medio / bajo del portafolio"
              />
              <SemaphorePieChart
                verdes={summary.casos_verdes}
                amarillos={summary.casos_amarillos}
                rojos={summary.casos_rojos}
              />
            </View>

            <View style={styles.section}>
              <SectionHeader title="Riesgo por ramo" subtitle="Puntaje medio 0–100" />
              <RiskBarChart
                rows={report?.riesgo_por_ramo || []}
                nameKey="ramo"
                barColor={colors.chart3}
                layout="vertical"
              />
            </View>

            <View style={styles.section}>
              <SectionHeader title="Proveedores con mayor alerta" subtitle="Puntaje medio" />
              <RiskBarChart
                rows={report?.top_proveedores || []}
                nameKey="id_proveedor"
                barColor={colors.chart4}
                layout="horizontal"
                limit={5}
              />
            </View>

            <View style={styles.section}>
              <SectionHeader title="Riesgo por ciudad" subtitle="Puntaje medio 0–100" />
              <RiskBarChart
                rows={report?.top_ciudades || []}
                nameKey="ciudad"
                barColor={colors.chart1}
                layout="vertical"
              />
            </View>

            <View style={styles.section}>
              <SectionHeader
                title="Casos prioritarios"
                subtitle="Top 10 por score de riesgo"
              />
              <View style={styles.casesList}>
                {(report?.top_casos || []).map((claim) => (
                  <View key={claim.id_siniestro} style={styles.caseRow}>
                    <View style={styles.caseTop}>
                      <Text style={textStyles.mono}>{claim.id_siniestro}</Text>
                      <RiskBadge level={claim.nivel_riesgo} />
                    </View>
                    <Text style={textStyles.body}>
                      {claim.ramo || 'Sin ramo'} · {claim.ciudad || 'Sin ciudad'}
                    </Text>
                    <View style={styles.caseBottom}>
                      <Text style={textStyles.label}>
                        Score {Math.round(Number(claim.score_final ?? 0))}
                      </Text>
                      <Text style={textStyles.bodyMedium}>
                        {formatCurrency(claim.monto_reclamado)}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            </View>

            {report?.ethics_note ? (
              <View style={styles.ethicsNote}>
                <Text style={[textStyles.body, styles.ethicsText]}>{report.ethics_note}</Text>
              </View>
            ) : null}
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: spacing.xxxl * 2,
    gap: spacing.lg,
  },
  hero: {
    backgroundColor: colors.primaryContainer,
    borderRadius: radius.xl,
    padding: spacing.xl,
    gap: spacing.sm,
  },
  brand: {
    fontFamily: fonts.sansBold,
    fontSize: 13,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    color: colors.brandSoft,
  },
  heroCopy: {
    color: '#c8d4ea',
  },
  apiHint: {
    ...textStyles.labelMono,
    color: '#8fa3c4',
    marginTop: spacing.sm,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  section: {
    backgroundColor: colors.surfaceLowest,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  savingsCard: {
    backgroundColor: colors.successContainer,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: '#b6e4c8',
    gap: spacing.xs,
  },
  savingsNote: {
    marginTop: spacing.sm,
    color: colors.onSuccessContainer,
  },
  casesList: {
    gap: spacing.md,
  },
  caseRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceLow,
    gap: spacing.xs,
  },
  caseTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  caseBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.xs,
  },
  ethicsNote: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.lg,
    backgroundColor: colors.surfaceLow,
  },
  ethicsText: {
    fontStyle: 'italic',
    color: colors.mutedForeground,
  },
  centerState: {
    alignItems: 'center',
    paddingVertical: spacing.xxxl,
    gap: spacing.md,
  },
  stateText: {
    textAlign: 'center',
  },
  errorCard: {
    backgroundColor: colors.errorContainer,
    borderRadius: radius.lg,
    padding: spacing.lg,
    gap: spacing.sm,
  },
  errorTitle: {
    ...textStyles.title,
    color: colors.onErrorContainer,
  },
  retryBtn: {
    marginTop: spacing.sm,
    alignSelf: 'flex-start',
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
  },
  retryText: {
    fontFamily: fonts.sansSemiBold,
    color: colors.primaryForeground,
    fontSize: 14,
  },
})
