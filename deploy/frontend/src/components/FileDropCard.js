import { createElement, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, shadows } from '../theme';

export default function FileDropCard({
  onPick,
  onDrop,
  picking = false,
  disabled = false,
  maxUploadMb = 20,
  maxAudioSeconds = 120,
}) {
  const [isDragging, setIsDragging] = useState(false);
  const inactive = picking || disabled;

  const preventDefault = (event) => {
    event?.preventDefault?.();
    event?.stopPropagation?.();
  };

  const handleDrop = (event) => {
    preventDefault(event);
    setIsDragging(false);
    if (inactive) return;
    const file = event?.nativeEvent?.dataTransfer?.files?.[0] || event?.dataTransfer?.files?.[0];
    if (file) onDrop?.(file);
  };

  const content = (
    <View style={[styles.card, isDragging && styles.dragging, inactive && styles.disabled]}>
      <View style={styles.iconWrap}>
        <Ionicons name={isDragging ? 'download-outline' : 'cloud-upload-outline'} size={25} color={colors.primary} />
      </View>
      <Text style={styles.title}>{isDragging ? 'Suelta el audio aquí' : 'Carga un audio en español'}</Text>
      <Text style={styles.description}>
        Arrastra un archivo a esta zona o selecciónalo desde tu dispositivo. Primero
        comprobaremos su formato, peso y duración.
      </Text>

      <View style={styles.formats}>
        <Text style={styles.formatsText}>WAV · MP3 · M4A · OGG · FLAC · WEBM</Text>
        <Text style={styles.limits}>
          Máx. {maxUploadMb} MB · entre 0.5 s y {Math.round(maxAudioSeconds / 60)} min
        </Text>
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Seleccionar archivo de audio"
        onPress={onPick}
        disabled={inactive}
        style={({ pressed }) => [styles.button, pressed && styles.pressed, inactive && styles.disabled]}
      >
        {picking ? <ActivityIndicator size="small" color={colors.white} /> : <Ionicons name="folder-open-outline" size={16} color={colors.white} />}
        <Text style={styles.buttonText}>{picking ? 'Abriendo selector…' : 'Seleccionar audio'}</Text>
      </Pressable>

      <Text style={styles.privacyText}>
        El resultado será temporal; el WAV y los datos asociados expiran automáticamente.
      </Text>
    </View>
  );

  if (Platform.OS !== 'web') return content;

  return createElement(
    'div',
    {
      'aria-label': 'Zona para soltar un archivo de audio',
      onDragEnter: (event) => {
        preventDefault(event);
        if (!inactive) setIsDragging(true);
      },
      onDragOver: preventDefault,
      onDragLeave: (event) => {
        preventDefault(event);
        setIsDragging(false);
      },
      onDrop: handleDrop,
      style: { width: '100%' },
    },
    content,
  );
}

const styles = StyleSheet.create({
  card: { width: '100%', maxWidth: 720, alignSelf: 'center', backgroundColor: colors.surface, borderRadius: 24, borderWidth: 1.5, borderColor: '#D7E4DF', borderStyle: 'dashed', padding: 28, alignItems: 'center', ...shadows.soft },
  dragging: { backgroundColor: colors.primarySoft, borderColor: colors.primary, borderStyle: 'solid' },
  iconWrap: { width: 58, height: 58, borderRadius: 19, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.primarySoft, marginBottom: 12 },
  title: { fontFamily: fonts.extrabold, fontSize: 20, letterSpacing: -0.45, color: colors.ink, textAlign: 'center' },
  description: { maxWidth: 480, fontFamily: fonts.medium, fontSize: 13.5, lineHeight: 20, color: colors.inkSoft, textAlign: 'center', marginTop: 7 },
  formats: { alignItems: 'center', gap: 3, marginTop: 15, marginBottom: 16 },
  formatsText: { fontFamily: fonts.bold, fontSize: 9.5, letterSpacing: 0.55, color: colors.primary },
  limits: { fontFamily: fonts.medium, fontSize: 10, color: colors.inkFaint },
  button: { minHeight: 47, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 14, paddingHorizontal: 18, backgroundColor: colors.primary, shadowColor: colors.primary, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.18, shadowRadius: 10, elevation: 3 },
  buttonText: { fontFamily: fonts.bold, fontSize: 12.5, color: colors.white },
  privacyText: { maxWidth: 430, fontFamily: fonts.medium, fontSize: 9.5, lineHeight: 14, color: colors.inkFaint, textAlign: 'center', marginTop: 14 },
  pressed: { opacity: 0.82 },
  disabled: { opacity: 0.6 },
});
