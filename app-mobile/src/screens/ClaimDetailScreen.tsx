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
import type { NativeStackScreenProps } from '@react-navigation/native-stack'
import {
  ApiClientError,
  getClaimDossier,
  type ClaimDossier,
} from '../lib/api'
import { formatCurrency, formatNumber } from '../lib/format'
import { colors, radius, spacing } from '../theme/tokens'
import { fonts, textStyles } from '../theme/typography'
import { RiskBadge } from '../components/RiskBadge'
import { SectionHeader } from '../components/SectionHeader'
import type { RootStackParamList } from '../navigation/types'

type Props = NativeStackScreenProps<RootStackParamList, 'ClaimDetail'>

export function ClaimDetailScreen({ route, navigation }: Props) {
  const { idSiniestro } = route.params
  const [dossier, setDossier] = useState<ClaimDossier | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<{ message: string; hint?: string | null } | null>(null)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)
    try {
      const data = await getClaimDossier(idSiniestro)
      setDossier(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido'
      const hint = err instanceof ApiClientError ? err.hint : null
      setError({ message, hint })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [idSiniestro])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    navigation.setOptions({ title: idSiniestro })
  }, [idSiniestro, navigation])

  return (
    <ScrollView
      style={styles.safe}
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
      {loading && !dossier ? (
        <View style={styles.centerState}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={textStyles.subtitle}>Cargando expediente…</Text>
        </View>
      ) : null}

      {error && !dossier ? (
        <View style={styles.errorCard}>
          <Text style={styles.errorTitle}>No se pudo cargar el caso</Text>
          <Text style={textStyles.body}>{error.message}</Text>
          {error.hint ? <Text style={textStyles.subtitle}>{error.hint}</Text> : null}
          <Pressable style={styles.retryBtn} onPress={() => void load()}>
            <Text style={styles.retryText}>Reintentar</Text>
          </Pressable>
        </View>
      ) : null}

      {dossier ? (
        <>
          <View style={styles.hero}>
            <View style={styles.heroTop}>
              <Text style={textStyles.mono}>{dossier.id_siniestro}</Text>
              <RiskBadge level={dossier.risk.nivel_riesgo} />
            </View>
            <Text style={styles.headline}>{dossier.headline}</Text>
            <Text style={styles.scoreLine}>
              Score {Math.round(Number(dossier.risk.score_final ?? 0))} / 100
            </Text>
          </View>

          {dossier.executive_takeaway ? (
            <View style={styles.section}>
              <SectionHeader title="Lectura ejecutiva" />
              <Text style={textStyles.body}>{dossier.executive_takeaway}</Text>
            </View>
          ) : null}

          <View style={styles.section}>
            <SectionHeader title="Contexto del siniestro" />
            <View style={styles.metaGrid}>
              <Meta label="Ramo" value={dossier.claim.ramo || 'N/D'} />
              <Meta label="Ciudad" value={dossier.claim.ciudad || 'N/D'} />
              <Meta label="Proveedor" value={dossier.claim.id_proveedor || 'N/D'} />
              <Meta label="Monto" value={formatCurrency(dossier.claim.monto_reclamado)} />
              <Meta label="Suma asegurada" value={formatCurrency(dossier.claim.suma_asegurada)} />
              <Meta label="Cobertura" value={dossier.claim.cobertura || 'N/D'} />
            </View>
          </View>

          <View style={styles.section}>
            <SectionHeader title="Riesgo y acción" />
            <Text style={textStyles.bodyMedium}>
              {dossier.risk.accion_sugerida || 'Revisión humana recomendada'}
            </Text>
            {dossier.main_driver?.componente ? (
              <Text style={[textStyles.label, styles.driver]}>
                Driver principal: {dossier.main_driver.componente}
                {dossier.main_driver.valor != null
                  ? ` (${formatNumber(dossier.main_driver.valor)})`
                  : ''}
              </Text>
            ) : null}
          </View>

          {dossier.investigation_summary || dossier.explanation ? (
            <View style={styles.section}>
              <SectionHeader title="Explicación" />
              <Text style={textStyles.body}>
                {dossier.investigation_summary || dossier.explanation}
              </Text>
            </View>
          ) : null}

          {(dossier.evidence || []).length > 0 ? (
            <View style={styles.section}>
              <SectionHeader title="Evidencias" subtitle="Señales que elevan el puntaje" />
              <View style={styles.evidenceList}>
                {dossier.evidence.slice(0, 8).map((item, index) => (
                  <View key={`${item.codigo || item.senal}-${index}`} style={styles.evidenceRow}>
                    <View style={styles.evidenceTop}>
                      <Text style={textStyles.labelMono}>
                        {item.codigo || item.senal || `Señal ${index + 1}`}
                      </Text>
                      {item.puntos != null ? (
                        <Text style={textStyles.bodyMedium}>+{item.puntos}</Text>
                      ) : null}
                    </View>
                    {item.mensaje ? <Text style={textStyles.body}>{item.mensaje}</Text> : null}
                  </View>
                ))}
              </View>
            </View>
          ) : null}

          {(dossier.recommended_review || []).length > 0 ? (
            <View style={styles.section}>
              <SectionHeader title="Próximos pasos" />
              {dossier.recommended_review.map((step, index) => (
                <Text key={`${step}-${index}`} style={[textStyles.body, styles.stepLine]}>
                  {index + 1}. {step}
                </Text>
              ))}
            </View>
          ) : null}

          {dossier.ethical_guardrail ? (
            <View style={styles.ethicsNote}>
              <Text style={[textStyles.body, styles.ethicsText]}>{dossier.ethical_guardrail}</Text>
            </View>
          ) : null}
        </>
      ) : null}
    </ScrollView>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metaItem}>
      <Text style={textStyles.labelMono}>{label}</Text>
      <Text style={textStyles.bodyMedium} numberOfLines={2}>
        {value}
      </Text>
    </View>
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
  heroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headline: {
    fontFamily: fonts.sansSemiBold,
    fontSize: 18,
    lineHeight: 24,
    color: colors.brandSoft,
  },
  scoreLine: {
    ...textStyles.labelMono,
    color: '#8fa3c4',
  },
  section: {
    backgroundColor: colors.surfaceLowest,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  metaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  metaItem: {
    width: '46%',
    gap: 2,
  },
  driver: {
    marginTop: spacing.sm,
  },
  evidenceList: {
    gap: spacing.md,
  },
  evidenceRow: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    backgroundColor: colors.surfaceLow,
    gap: spacing.xs,
  },
  evidenceTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stepLine: {
    marginBottom: spacing.sm,
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
