import { Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, shadows } from '../theme';
import { formatBytes, formatDuration } from '../utils/audio';
import AudioPlayer from './AudioPlayer';

export default function SelectedAudioBubble({
  file,
  onRemove,
  disabled = false,
}) {
  return (
    <LinearGradient
      colors={['#157065', '#0A4A43']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.bubble}
    >
      <View style={styles.header}>
        <View style={styles.icon}>
          <Ionicons name="musical-notes" size={15} color={colors.white} />
        </View>
        <View style={styles.fileInfo}>
          <Text numberOfLines={1} style={styles.name}>
            {file.name}
          </Text>
          <Text style={styles.meta}>
            Audio original · Español · {formatBytes(file.size)}
            {file.durationSec ? ` · ${formatDuration(file.durationSec)}` : ''}
          </Text>
        </View>
        {!disabled ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Quitar audio seleccionado"
            onPress={onRemove}
            hitSlop={8}
            style={({ pressed }) => [styles.remove, pressed && styles.pressed]}
          >
            <Ionicons name="close" size={15} color="rgba(255,255,255,0.8)" />
          </Pressable>
        ) : null}
      </View>

      <View style={styles.player}>
        <AudioPlayer
          source={file.uri}
          duration={file.durationSec || 0}
          variant="dark"
          label="audio original"
        />
      </View>

      <View style={styles.footer}>
        <Ionicons name="lock-closed-outline" size={10} color="rgba(255,255,255,0.5)" />
        <Text style={styles.footerText}>Se enviará al motor local para traducirse</Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  bubble: {
    width: '100%',
    maxWidth: 480,
    alignSelf: 'flex-end',
    borderRadius: 22,
    borderTopRightRadius: 7,
    padding: 14,
    ...shadows.soft,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
  },
  icon: {
    width: 34,
    height: 34,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.15)',
  },
  fileInfo: {
    flex: 1,
  },
  name: {
    fontFamily: fonts.bold,
    fontSize: 13,
    color: colors.white,
  },
  meta: {
    fontFamily: fonts.medium,
    fontSize: 9.5,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 2,
  },
  remove: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.12)',
  },
  pressed: {
    opacity: 0.7,
  },
  player: {
    marginTop: 12,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 9,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  footerText: {
    fontFamily: fonts.medium,
    fontSize: 9,
    color: 'rgba(255,255,255,0.5)',
  },
});
