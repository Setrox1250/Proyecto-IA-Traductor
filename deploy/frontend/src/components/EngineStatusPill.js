import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts } from '../theme';

function resolveState(status, error, loading) {
  if (error) return { label: 'Sin conexión', tone: 'error', dot: colors.danger };
  if (!status && loading) {
    return { label: 'Conectando…', tone: 'neutral', dot: colors.inkFaint };
  }
  if (status?.pipeline?.busy) {
    return { label: 'Procesando audio', tone: 'busy', dot: colors.accent };
  }
  if (status?.status === 'degraded') {
    return { label: 'Licencia pendiente', tone: 'warning', dot: colors.accent };
  }
  if (status?.pipeline?.ready) {
    return {
      label: status.pipeline.warm ? 'Motor listo' : 'Motor disponible',
      tone: 'ok',
      dot: colors.online,
    };
  }
  return { label: 'Estado desconocido', tone: 'neutral', dot: colors.inkFaint };
}

export default function EngineStatusPill({ status, error, loading, onRefresh }) {
  const state = resolveState(status, error, loading);
  const toneStyle =
    state.tone === 'error'
      ? styles.error
      : state.tone === 'ok'
        ? styles.ok
        : state.tone === 'warning'
          ? styles.warning
          : state.tone === 'busy'
            ? styles.busy
            : styles.neutral;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${state.label}. Actualizar estado`}
      onPress={onRefresh}
      style={({ pressed }) => [styles.pill, toneStyle, pressed && styles.pressed]}
    >
      <View style={[styles.dot, { backgroundColor: state.dot }]} />
      <Text style={styles.label}>{state.label}</Text>
      {loading ? (
        <ActivityIndicator size={10} color={colors.inkSoft} />
      ) : (
        <Ionicons name="refresh" size={11} color={colors.inkSoft} />
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderWidth: 1,
  },
  ok: {
    backgroundColor: '#E8F5EF',
    borderColor: '#CDEBDF',
  },
  busy: {
    backgroundColor: colors.accentSoft,
    borderColor: '#F5DCC2',
  },
  warning: {
    backgroundColor: colors.accentSoft,
    borderColor: '#F5DCC2',
  },
  error: {
    backgroundColor: '#FDEDEA',
    borderColor: '#F6D4CD',
  },
  neutral: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.line,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  label: {
    fontFamily: fonts.bold,
    fontSize: 10.5,
    color: colors.ink,
    letterSpacing: 0.1,
  },
  pressed: {
    opacity: 0.7,
  },
});
