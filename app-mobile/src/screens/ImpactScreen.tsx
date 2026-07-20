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
import { useNavigation } from '@react-navigation/native'
import type { CompositeNavigationProp } from '@react-navigation/native'
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs'
import type { NativeStackNavigationProp } from '@react-navigation/native-stack'
import { SafeAreaView } from 'react-native-safe-area-context'
import {
  ApiClientError,
  getBusinessImpact,
  getStarCases,
  type BusinessImpact,
  type StarCase,
  type StarCasesResponse,
} from '../lib/api'
import { formatCurrency, formatNumber } from '../lib/format'
import { colors, radius, spacing } from '../theme/tokens'
import { fonts, textStyles } from '../theme/typography'
import { KpiCard } from '../components/KpiCard'
import { RiskBadge } from '../components/RiskBadge'
import { SectionHeader } from '../components/SectionHeader'
import type { RootStackParamList, RootTabParamList } from '../navigation/types'

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<RootTabParamList, 'Impact'>,
  NativeStackNavigationProp<RootStackParamList>
>

export function ImpactScreen() {
  const navigation = useNavigation<Nav>()
  const [impact, setImpact] = useState<BusinessImpact | null>(null)
  const [stars, setStars] = useState<StarCasesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<{ message: string; hint?: string | null } | null>(null)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError(null)
    try {
      const [impactData, starData] = await Promise.all([
        getBusinessImpact(0.1),
        getStarCases(),
      ])
      setImpact(impactData)
      setStars(starData)
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

  const openCase = (id: string) => {
    navigation.navigate('ClaimDetail', { idSiniestro: id })
  }

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
          <Text style={textStyles.display}>Impacto ejecutivo</Text>
          <Text style={[textStyles.subtitle, styles.heroCopy]}>
            Exposición priorizada y casos estrella para revisión humana.
          </Text>
        </View>

        {loading && !impact ? (
          <View style={styles.centerState}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={textStyles.subtitle}>Preparando impacto…</Text>
          </View>
        ) : null}

        {error && !impact ? (
          <View style={styles.errorCard}>
            <Text style={styles.errorTitle}>No se pudo cargar el impacto</Text>
            <Text style={textStyles.body}>{error.message}</Text>
            {error.hint ? <Text style={textStyles.subtitle}>{error.hint}</Text> : null}
            <Pressable style={styles.retryBtn} onPress={() => void load()}>
              <Text style={styles.retryText}>Reintentar</Text>
            </Pressable>
          </View>
        ) : null}

        {impact ? (
          <>
            <View style={styles.kpiGrid}>
              <KpiCard label="Siniestros" value={formatNumber(impact.total_siniestros)} />
              <KpiCard
                label="Casos rojos"
                value={formatNumber(impact.casos_rojos)}
                accent="rojo"
              />
              <KpiCard
                label="A revisar primero"
                value={formatNumber(impact.casos_a_revisar_top_percent)}
                hint={`Top ${(impact.porcentaje_revision * 100).toFixed(0)}%`}
                accent="amarillo"
              />
              <KpiCard
                label="Monto priorizado"
                value={formatCurrency(impact.monto_priorizado_top_percent)}
                accent="verde"
              />
            </View>

            <View style={styles.criteriaCard}>
              <Text style={textStyles.labelMono}>Criterio de uso</Text>
              <Text style={[textStyles.body, styles.criteriaBody]}>
                RastroSeguro no promete ahorros automáticos ni confirma fraude. Señala prioridades
                para revisión humana y muestra evidencia verificable.
              </Text>
              {impact.mensaje ? (
                <Text style={[textStyles.body, styles.impactMsg]}>{impact.mensaje}</Text>
              ) : null}
            </View>
          </>
        ) : null}

        {(stars?.cases || []).length > 0 ? (
          <View style={styles.section}>
            <SectionHeader
              title="Casos prioritarios"
              subtitle="Toca un caso para ver el expediente"
            />
            <View style={styles.casesList}>
              {(stars?.cases || []).map((item: StarCase) => (
                <Pressable
                  key={`${item.tipo}-${item.id_siniestro}`}
                  style={({ pressed }) => [styles.caseRow, pressed && styles.casePressed]}
                  onPress={() => openCase(item.id_siniestro)}
                >
                  <View style={styles.caseTop}>
                    <Text style={styles.tipo}>{item.tipo}</Text>
                    <RiskBadge level={item.nivel_riesgo} />
                  </View>
                  <Text style={textStyles.mono}>{item.id_siniestro}</Text>
                  <Text style={textStyles.body}>
                    {item.ramo || 'Sin ramo'} · {item.ciudad || 'Sin ciudad'}
                  </Text>
                  <Text style={[textStyles.body, styles.why]}>{item.por_que_destaca}</Text>
                  <View style={styles.caseBottom}>
                    <Text style={textStyles.label}>
                      Score {Math.round(Number(item.score_final ?? 0))}
                    </Text>
                    <Text style={textStyles.bodyMedium}>
                      {formatCurrency(item.monto_reclamado)}
                    </Text>
                  </View>
                </Pressable>
              ))}
            </View>
          </View>
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
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  criteriaCard: {
    backgroundColor: colors.surfaceLowest,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.lg,
    gap: spacing.sm,
  },
  criteriaBody: {
    color: colors.mutedForeground,
  },
  impactMsg: {
    marginTop: spacing.sm,
    fontStyle: 'italic',
    color: colors.mutedForeground,
    backgroundColor: colors.surfaceLow,
    padding: spacing.md,
    borderRadius: radius.md,
  },
  section: {
    backgroundColor: colors.surfaceLowest,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
    padding: spacing.lg,
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
  casePressed: {
    opacity: 0.85,
    backgroundColor: colors.accent,
  },
  caseTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tipo: {
    ...textStyles.labelMono,
    backgroundColor: colors.surfaceHigh,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    overflow: 'hidden',
  },
  why: {
    marginTop: spacing.xs,
    color: colors.mutedForeground,
  },
  caseBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.xs,
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
