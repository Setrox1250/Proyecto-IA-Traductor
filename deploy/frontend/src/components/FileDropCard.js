import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, shadows } from '../theme';

export default function FileDropCard({
  onPick,
  picking = false,
  maxUploadMb = 20,
  maxAudioSeconds = 120,
}) {
  return (
    <View style={styles.card}>
      <View style={styles.iconWrap}>
        <Ionicons name="cloud-upload-outline" size={24} color={colors.primary} />
      </View>
      <Text style={styles.title}>Sube una nota de voz en español</Text>
      <Text style={styles.description}>
        Hilo la transcribirá, la traducirá al inglés y generará una nueva voz
        usando el audio como referencia.
      </Text>

      <View style={styles.formats}>
        <Text style={styles.formatsText}>
          WAV · MP3 · M4A · OGG · FLAC · WEBM
        </Text>
        <Text style={styles.limits}>
          Máx. {maxUploadMb} MB · {Math.round(maxAudioSeconds / 60)} min
        </Text>
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Seleccionar archivo de audio"
        onPress={onPick}
        disabled={picking}
        style={({ pressed }) => [
          styles.button,
          pressed && styles.pressed,
          picking && styles.disabled,
        ]}
      >
        {picking ? (
          <ActivityIndicator size="small" color={colors.white} />
        ) : (
          <Ionicons name="folder-open-outline" size={16} color={colors.white} />
        )}
        <Text style={styles.buttonText}>
          {picking ? 'Abriendo selector…' : 'Seleccionar audio'}
        </Text>
      </Pressable>

      <View style={styles.privacyRow}>
        <Ionicons name="shield-checkmark-outline" size={12} color={colors.inkFaint} />
        <Text style={styles.privacyText}>
          El resultado es temporal y el audio no se guarda de forma permanente.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    maxWidth: 660,
    backgroundColor: colors.surface,
    borderRadius: 24,
    borderWidth: 1.5,
    borderColor: '#D7E4DF',
    borderStyle: 'dashed',
    padding: 24,
    alignItems: 'center',
    ...shadows.soft,
  },
  iconWrap: {
    width: 56,
    height: 56,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primarySoft,
    marginBottom: 11,
  },
  title: {
    fontFamily: fonts.extrabold,
    fontSize: 19,
    letterSpacing: -0.4,
    color: colors.ink,
    textAlign: 'center',
  },
  description: {
    maxWidth: 430,
    fontFamily: fonts.medium,
    fontSize: 13.5,
    lineHeight: 20,
    color: colors.inkSoft,
    textAlign: 'center',
    marginTop: 6,
  },
  formats: {
    alignItems: 'center',
    gap: 2,
    marginTop: 13,
    marginBottom: 14,
  },
  formatsText: {
    fontFamily: fonts.bold,
    fontSize: 9.5,
    letterSpacing: 0.55,
    color: colors.primary,
  },
  limits: {
    fontFamily: fonts.medium,
    fontSize: 10,
    color: colors.inkFaint,
  },
  button: {
    minHeight: 47,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
    borderRadius: 14,
    paddingHorizontal: 18,
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.18,
    shadowRadius: 10,
    elevation: 3,
  },
  buttonText: {
    fontFamily: fonts.bold,
    fontSize: 12.5,
    color: colors.white,
  },
  pressed: {
    opacity: 0.82,
  },
  disabled: {
    opacity: 0.7,
  },
  privacyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    marginTop: 12,
  },
  privacyText: {
    fontFamily: fonts.medium,
    fontSize: 9.5,
    color: colors.inkFaint,
    textAlign: 'center',
    flexShrink: 1,
  },
});
