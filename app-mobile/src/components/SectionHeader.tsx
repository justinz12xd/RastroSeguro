import { StyleSheet, Text, View } from 'react-native'
import { colors, spacing } from '../theme/tokens'
import { textStyles } from '../theme/typography'

type Props = {
  title: string
  subtitle?: string
}

export function SectionHeader({ title, subtitle }: Props) {
  return (
    <View style={styles.wrap}>
      <Text style={textStyles.title}>{title}</Text>
      {subtitle ? <Text style={[textStyles.subtitle, styles.subtitle]}>{subtitle}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    paddingBottom: spacing.sm,
  },
  subtitle: {
    marginTop: spacing.xs,
  },
})
