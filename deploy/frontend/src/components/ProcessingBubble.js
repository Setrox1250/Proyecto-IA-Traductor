import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, shadows } from '../theme';

const STAGES = [
  { icon: 'mic-outline', label: 'Whisper · ASR' },
  { icon: 'language-outline', label: 'MarianMT · ES→EN' },
  { icon: 'volume-high-outline', label: 'XTTS · voz' },
];

export default function ProcessingBubble({ elapsedSeconds = 0 }) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.spinner}>
          <ActivityIndicator size="small" color={colors.primary} />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title}>Procesando tu audio…</Text>
          <Text style={styles.timer}>{Math.floor(elapsedSeconds)} s transcurridos</Text>
        </View>
      </View>

      <View style={styles.track}>
        <View style={styles.trackFill} />
      </View>

      <Text style={styles.description}>
        La transcripción, la traducción y la síntesis se ejecutan en secuencia.
        La primera petición puede tardar más mientras se cargan los modelos.
      </Text>

      <View style={styles.stages}>
        {STAGES.map((stage) => (
          <View key={stage.label} style={styles.stage}>
            <Ionicons name={stage.icon} size={11} color={colors.primary} />
            <Text style={styles.stageText}>{stage.label}</Text>
          </View>
        ))}
      </View>

      <View style={styles.note}>
        <Ionicons name="information-circle-outline" size={12} color={colors.inkFaint} />
        <Text style={styles.noteText}>
          No es tiempo real. No cierres esta pestaña mientras el motor trabaja.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    maxWidth: 560,
    backgroundColor: colors.surface,
    borderRadius: 22,
    borderTopLeftRadius: 7,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.045)',
    padding: 15,
    ...shadows.soft,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  spinner: {
    width: 38,
    height: 38,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontFamily: fonts.extrabold,
    fontSize: 14.5,
    letterSpacing: -0.2,
    color: colors.ink,
  },
  timer: {
    fontFamily: fonts.medium,
    fontSize: 10.5,
    color: colors.inkFaint,
    marginTop: 2,
  },
  track: {
    height: 4,
    borderRadius: 3,
    backgroundColor: colors.primarySoft,
    marginTop: 13,
    overflow: 'hidden',
  },
  trackFill: {
    width: '42%',
    height: '100%',
    borderRadius: 3,
    backgroundColor: colors.accent,
  },
  description: {
    fontFamily: fonts.medium,
    fontSize: 12,
    lineHeight: 18,
    color: colors.inkSoft,
    marginTop: 11,
  },
  stages: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
    marginTop: 11,
  },
  stage: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: colors.primarySoft,
  },
  stageText: {
    fontFamily: fonts.bold,
    fontSize: 9,
    color: colors.primary,
  },
  note: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 11,
    paddingTop: 9,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  noteText: {
    flex: 1,
    fontFamily: fonts.medium,
    fontSize: 9.5,
    lineHeight: 13,
    color: colors.inkFaint,
  },
});
