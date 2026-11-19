import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

import { apiUrl } from '../api/client';
import { colors, fonts, shadows } from '../theme';
import {
  formatSeconds,
  formatSimilarity,
  formatTime,
} from '../utils/audio';
import { downloadAudio } from '../utils/download';
import AudioPlayer from './AudioPlayer';

function Chip({ icon, label, value }) {
  return (
    <View style={styles.chip}>
      <Ionicons name={icon} size={11} color={colors.inkSoft} />
      <Text style={styles.chipLabel}>{label}</Text>
      <Text style={styles.chipValue}>{value}</Text>
    </View>
  );
}

function Timing({ label, value }) {
  return (
    <View style={styles.timing}>
      <Text style={styles.timingLabel}>{label}</Text>
      <Text style={styles.timingValue}>{formatSeconds(value)}</Text>
    </View>
  );
}

export default function ResultCard({ result }) {
  const [downloading, setDownloading] = useState(false);
  const [showSupportId, setShowSupportId] = useState(false);
  const subtitleTime = formatTime(result.created_at);
  const expiresAt = formatTime(result.expires_at);

  const handleDownload = async () => {
    if (downloading) return;
    setDownloading(true);
    try {
      await downloadAudio(
        apiUrl(result.audio.download_url || result.audio.url),
        result.audio.filename,
      );
    } finally {
      setDownloading(false);
    }
  };

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.check}>
          <Ionicons name="checkmark" size={15} color={colors.white} />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title}>Traducción completada</Text>
          <Text style={styles.subtitle}>
            {subtitleTime ? `${subtitleTime} · ` : ''}
            {formatSeconds(result.timings.total_sec)} de procesamiento
          </Text>
        </View>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>ES → EN</Text>
        </View>
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <View style={[styles.lang, styles.langEs]}>
            <Text style={[styles.langText, styles.langTextEs]}>ES</Text>
          </View>
          <Text style={styles.sectionLabel}>Transcripción · Español</Text>
        </View>
        <Text style={styles.transcription}>{result.transcription_es}</Text>
      </View>

      <View style={styles.divider}>
        <View style={styles.line} />
        <View style={styles.arrow}>
          <Ionicons name="arrow-down" size={11} color={colors.lavender} />
        </View>
        <View style={styles.line} />
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <View style={[styles.lang, styles.langEn]}>
            <Text style={[styles.langText, styles.langTextEn]}>EN</Text>
          </View>
          <Text style={[styles.sectionLabel, styles.sectionLabelEn]}>
            Traducción · English
          </Text>
        </View>
        <Text style={styles.translation}>{result.translation_en}</Text>
      </View>

      <LinearGradient
        colors={['#12685D', '#083F39']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.audioCard}
      >
        <View style={styles.audioHeader}>
          <View style={styles.audioIcon}>
            <Ionicons name="volume-high" size={14} color={colors.white} />
          </View>
          <View style={styles.audioTitle}>
            <Text style={styles.audioTitleText}>WAV generado en inglés</Text>
            <Text style={styles.audioSubtitle}>
              Voz condicionada por la referencia · XTTS-v2 · {result.audio.sample_rate / 1000} kHz
            </Text>
          </View>
          <View style={styles.waveBadge}>
            <Ionicons name="analytics-outline" size={13} color={colors.accent} />
          </View>
        </View>

        <View style={styles.audioPlayer}>
          <AudioPlayer
            source={apiUrl(result.audio.url)}
            duration={result.audio.duration_sec}
            variant="dark"
            label="audio traducido"
          />
        </View>

        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Descargar audio traducido"
          onPress={handleDownload}
          disabled={downloading}
          style={({ pressed }) => [
            styles.download,
            pressed && styles.pressed,
            downloading && styles.disabled,
          ]}
        >
          <Ionicons
            name={downloading ? 'hourglass-outline' : 'download-outline'}
            size={15}
            color={colors.primaryDeep}
          />
          <Text style={styles.downloadText}>
            {downloading ? 'Preparando…' : 'Descargar WAV'}
          </Text>
          <Text style={styles.downloadSize}>
            {Math.round(result.audio.duration_sec)} s
          </Text>
        </Pressable>
      </LinearGradient>

      <View style={styles.metrics}>
        <Chip
          icon="analytics-outline"
          label="Similitud ECAPA"
          value={formatSimilarity(result.speaker_similarity)}
        />
        <Chip
          icon="time-outline"
          label="Audio original"
          value={formatSeconds(result.input?.duration_sec)}
        />
        <Chip
          icon="volume-high-outline"
          label="WAV generado"
          value={formatSeconds(result.audio.duration_sec)}
        />
        <Chip
          icon="time-outline"
          label="Proceso total"
          value={formatSeconds(result.timings.total_sec)}
        />
        <Chip
          icon="server-outline"
          label="Modelo NMT"
          value="MarianMT base"
        />
      </View>

      <View style={styles.timingPanel}>
        <Text style={styles.timingTitle}>Tiempos del pipeline</Text>
        <View style={styles.timingGrid}>
          <Timing label="Preparación" value={result.timings.preprocessing_sec} />
          <Timing label="Transcripción" value={result.timings.asr_sec} />
          <Timing label="Traducción" value={result.timings.translation_sec} />
          <Timing label="Síntesis WAV" value={result.timings.xtts_sec} />
          <Timing label="ECAPA" value={result.timings.speaker_evaluation_sec} />
          <Timing label="API" value={result.timings.api_sec} />
        </View>
      </View>

      <Text style={styles.disclaimer}>
        La similitud ECAPA es una métrica objetiva de embeddings, no un porcentaje
        de identidad. La voz condicionada por la referencia es aproximada y el proceso
        no es en tiempo real.
      </Text>
      <View style={styles.supportRow}>
        <Text style={styles.expiryText}>
          {expiresAt ? `Disponible hasta aprox. ${expiresAt}.` : 'Resultado temporal.'}
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Mostrar referencia de soporte"
          onPress={() => setShowSupportId((value) => !value)}
        >
          <Text style={styles.supportButton}>
            {showSupportId ? 'Ocultar referencia' : 'Referencia de soporte'}
          </Text>
        </Pressable>
      </View>
      {showSupportId ? <Text style={styles.supportId}>ID: {result.id}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    maxWidth: 680,
    backgroundColor: colors.surface,
    borderRadius: 24,
    borderTopLeftRadius: 7,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.045)',
    padding: 16,
    ...shadows.card,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    marginBottom: 14,
  },
  check: {
    width: 30,
    height: 30,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.online,
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontFamily: fonts.extrabold,
    fontSize: 15,
    letterSpacing: -0.2,
    color: colors.ink,
  },
  subtitle: {
    fontFamily: fonts.medium,
    fontSize: 10,
    color: colors.inkFaint,
    marginTop: 2,
  },
  badge: {
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: colors.lavenderSoft,
  },
  badgeText: {
    fontFamily: fonts.extrabold,
    fontSize: 8.5,
    letterSpacing: 0.5,
    color: colors.lavender,
  },
  section: {
    gap: 5,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  lang: {
    width: 22,
    height: 16,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  langEs: {
    backgroundColor: colors.accentSoft,
  },
  langEn: {
    backgroundColor: colors.lavenderSoft,
  },
  langText: {
    fontFamily: fonts.extrabold,
    fontSize: 8,
    letterSpacing: 0.4,
  },
  langTextEs: {
    color: '#B36B2C',
  },
  langTextEn: {
    color: colors.lavender,
  },
  sectionLabel: {
    fontFamily: fonts.bold,
    fontSize: 9.5,
    letterSpacing: 0.55,
    textTransform: 'uppercase',
    color: colors.inkFaint,
  },
  sectionLabelEn: {
    color: colors.lavender,
  },
  transcription: {
    fontFamily: fonts.medium,
    fontSize: 14,
    lineHeight: 21,
    color: colors.inkSoft,
  },
  translation: {
    fontFamily: fonts.semibold,
    fontSize: 15,
    lineHeight: 22,
    color: colors.ink,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginVertical: 12,
  },
  line: {
    height: 1,
    flex: 1,
    backgroundColor: colors.lavenderLine,
  },
  arrow: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.lavenderSoft,
  },
  audioCard: {
    borderRadius: 18,
    padding: 12,
    marginTop: 15,
  },
  audioHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 11,
  },
  audioIcon: {
    width: 30,
    height: 30,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.14)',
  },
  audioTitle: {
    flex: 1,
  },
  audioTitleText: {
    fontFamily: fonts.bold,
    fontSize: 12,
    color: colors.white,
  },
  audioSubtitle: {
    fontFamily: fonts.medium,
    fontSize: 9,
    color: 'rgba(255,255,255,0.55)',
    marginTop: 1,
  },
  waveBadge: {
    width: 26,
    height: 26,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.09)',
  },
  audioPlayer: {
    marginBottom: 12,
  },
  download: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 11,
    paddingHorizontal: 10,
    paddingVertical: 7,
    backgroundColor: colors.white,
  },
  downloadText: {
    flex: 1,
    fontFamily: fonts.bold,
    fontSize: 10.5,
    color: colors.primaryDeep,
  },
  downloadSize: {
    fontFamily: fonts.bold,
    fontSize: 9,
    color: colors.inkFaint,
  },
  pressed: {
    opacity: 0.8,
  },
  disabled: {
    opacity: 0.7,
  },
  metrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 11,
  },
  timingPanel: {
    marginTop: 13,
    padding: 11,
    borderRadius: 14,
    backgroundColor: colors.surfaceMuted,
  },
  timingTitle: {
    fontFamily: fonts.bold,
    fontSize: 10,
    color: colors.inkSoft,
    marginBottom: 8,
  },
  timingGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },
  timing: {
    minWidth: 88,
    flexGrow: 1,
  },
  timingLabel: {
    fontFamily: fonts.medium,
    fontSize: 8.5,
    color: colors.inkFaint,
  },
  timingValue: {
    fontFamily: fonts.extrabold,
    fontSize: 10,
    color: colors.inkSoft,
    marginTop: 1,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.surfaceMuted,
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  chipLabel: {
    fontFamily: fonts.medium,
    fontSize: 9,
    color: colors.inkFaint,
  },
  chipValue: {
    fontFamily: fonts.extrabold,
    fontSize: 9,
    color: colors.inkSoft,
  },
  disclaimer: {
    fontFamily: fonts.medium,
    fontSize: 9,
    lineHeight: 13,
    color: colors.inkFaint,
    marginTop: 9,
  },
  supportRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    marginTop: 9,
  },
  expiryText: {
    flex: 1,
    fontFamily: fonts.medium,
    fontSize: 8.5,
    color: colors.inkFaint,
  },
  supportButton: {
    fontFamily: fonts.bold,
    fontSize: 8.5,
    color: colors.primary,
  },
  supportId: {
    fontFamily: fonts.medium,
    fontSize: 8.5,
    color: colors.inkFaint,
    marginTop: 4,
  },
});
