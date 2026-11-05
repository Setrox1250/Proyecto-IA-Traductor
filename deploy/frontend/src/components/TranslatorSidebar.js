import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, shadows } from '../theme';
import BrandMark from './BrandMark';
import EngineStatusPill from './EngineStatusPill';

const STEPS = [
  { icon: 'cloud-upload-outline', title: 'Sube el audio', text: 'Una nota de voz en español.' },
  { icon: 'language-outline', title: 'Hilo lo traduce', text: 'Whisper, MarianMT y XTTS-v2.' },
  { icon: 'headset-outline', title: 'Escucha y descarga', text: 'Voz en inglés lista en WAV.' },
];

export default function TranslatorSidebar({
  status,
  statusError,
  statusLoading,
  onRefreshStatus,
  limits,
}) {
  return (
    <View style={styles.sidebar}>
      <View style={styles.brandRow}>
        <BrandMark size={46} />
        <View>
          <Text style={styles.brand}>hilo</Text>
          <Text style={styles.tagline}>TRADUCTOR DE VOZ ES → EN</Text>
        </View>
      </View>

      <View style={styles.engineCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.kicker}>MOTOR DE TRADUCCIÓN</Text>
          <Ionicons name="pulse-outline" size={14} color={colors.primary} />
        </View>
        <EngineStatusPill
          status={status}
          error={statusError}
          loading={statusLoading}
          onRefresh={onRefreshStatus}
        />
        <View style={styles.engineMeta}>
          <View style={styles.metaRow}>
            <Ionicons name="hardware-chip-outline" size={12} color={colors.inkFaint} />
            <Text style={styles.metaText}>
              {status?.pipeline?.gpu?.available
                ? status.pipeline.gpu.name
                : 'Procesamiento en CPU'}
            </Text>
          </View>
          <View style={styles.metaRow}>
            <Ionicons name="layers-outline" size={12} color={colors.inkFaint} />
            <Text style={styles.metaText}>
              Inferencia secuencial · {status?.pipeline?.mode || 'pendiente'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.stepsCard}>
        <Text style={styles.sectionTitle}>Cómo funciona</Text>
        {STEPS.map((step, index) => (
          <View key={step.title} style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>{index + 1}</Text>
            </View>
            <View style={styles.stepCopy}>
              <Text style={styles.stepTitle}>{step.title}</Text>
              <Text style={styles.stepText}>{step.text}</Text>
            </View>
            <Ionicons name={step.icon} size={15} color={colors.primaryBright} />
          </View>
        ))}
      </View>

      <View style={styles.privacyCard}>
        <View style={styles.privacyHeader}>
          <View style={styles.privacyIcon}>
            <Ionicons name="shield-checkmark" size={14} color={colors.primary} />
          </View>
          <Text style={styles.privacyTitle}>Privacidad por diseño</Text>
        </View>
        <Text style={styles.privacyText}>
          Los audios se procesan localmente y los resultados expiran
          automáticamente. No hay cuentas ni almacenamiento permanente.
        </Text>
      </View>

      <View style={styles.spacer} />

      <View style={styles.footer}>
        <Text style={styles.limits}>
          Límites: {limits.maxUploadMb} MB · {Math.round(limits.maxAudioSeconds / 60)} min
        </Text>
        <Text style={styles.footerText}>
          Prototipo académico. Clonación aproximada, no tiempo real.
        </Text>
        <Text style={styles.licenseText}>
          XTTS-v2 se usa bajo CPML. Revisa la licencia antes de redistribuir.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  sidebar: {
    width: 300,
    paddingVertical: 6,
    paddingRight: 2,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    marginBottom: 22,
  },
  brand: {
    fontFamily: fonts.extrabold,
    fontSize: 25,
    lineHeight: 28,
    letterSpacing: -1.3,
    color: colors.ink,
  },
  tagline: {
    fontFamily: fonts.bold,
    fontSize: 8,
    letterSpacing: 1.15,
    color: colors.inkFaint,
    marginTop: 1,
  },
  engineCard: {
    backgroundColor: colors.surface,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.045)',
    padding: 14,
    ...shadows.soft,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  kicker: {
    fontFamily: fonts.extrabold,
    fontSize: 8.5,
    letterSpacing: 1.1,
    color: colors.inkFaint,
  },
  engineMeta: {
    gap: 6,
    marginTop: 11,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colors.line,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  metaText: {
    flex: 1,
    fontFamily: fonts.medium,
    fontSize: 9.5,
    color: colors.inkFaint,
  },
  stepsCard: {
    marginTop: 16,
    backgroundColor: 'rgba(255,255,255,0.55)',
    borderRadius: 22,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.04)',
    padding: 14,
  },
  sectionTitle: {
    fontFamily: fonts.extrabold,
    fontSize: 13,
    color: colors.ink,
    marginBottom: 10,
    letterSpacing: -0.2,
  },
  step: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    paddingVertical: 6,
  },
  stepNumber: {
    width: 21,
    height: 21,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
  },
  stepNumberText: {
    fontFamily: fonts.extrabold,
    fontSize: 8.5,
    color: colors.primary,
  },
  stepCopy: {
    flex: 1,
  },
  stepTitle: {
    fontFamily: fonts.bold,
    fontSize: 11,
    color: colors.ink,
  },
  stepText: {
    fontFamily: fonts.medium,
    fontSize: 9,
    color: colors.inkFaint,
    marginTop: 1,
  },
  privacyCard: {
    marginTop: 14,
    borderRadius: 18,
    padding: 12,
    backgroundColor: colors.primarySoft,
  },
  privacyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 5,
  },
  privacyIcon: {
    width: 22,
    height: 22,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.7)',
  },
  privacyTitle: {
    fontFamily: fonts.bold,
    fontSize: 10.5,
    color: colors.primaryDeep,
  },
  privacyText: {
    fontFamily: fonts.medium,
    fontSize: 9.5,
    lineHeight: 14,
    color: '#46756D',
  },
  spacer: {
    flex: 1,
    minHeight: 12,
  },
  footer: {
    gap: 2,
    paddingTop: 12,
  },
  limits: {
    fontFamily: fonts.bold,
    fontSize: 9,
    color: colors.inkSoft,
  },
  footerText: {
    fontFamily: fonts.medium,
    fontSize: 8.5,
    color: colors.inkFaint,
  },
  licenseText: {
    fontFamily: fonts.medium,
    fontSize: 8,
    lineHeight: 11,
    color: colors.inkFaint,
    marginTop: 3,
  },
});
