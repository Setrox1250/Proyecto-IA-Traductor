import { useEffect } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';

import { colors, fonts } from '../theme';
import { formatDuration } from '../utils/audio';
import Waveform from './Waveform';

export default function AudioPlayer({
  source,
  duration = 0,
  variant = 'light',
  label = 'Audio',
}) {
  const player = useAudioPlayer(undefined, { updateInterval: 250 });
  const status = useAudioPlayerStatus(player);
  const isDark = variant === 'dark';

  useEffect(() => {
    if (!source) return;
    try {
      player.replace(source);
    } catch {
      // El error de carga se refleja en el estado del reproductor.
    }
  }, [player, source]);

  const total = status.duration || duration || 0;
  const current = Math.min(status.currentTime || 0, total || Infinity);
  const progress = total > 0 ? current / total : 0;
  const isPlaying = Boolean(status.playing);

  const toggle = () => {
    if (!source) return;
    try {
      if (isPlaying) {
        player.pause();
        return;
      }
      if (status.didJustFinish || (total > 0 && current >= total - 0.05)) {
        player.seekTo(0);
      }
      player.play();
    } catch {
      // Los controles permanecen inactivos si el navegador bloquea la reproducción.
    }
  };

  return (
    <View style={styles.row}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={isPlaying ? `Pausar ${label}` : `Reproducir ${label}`}
        onPress={toggle}
        style={({ pressed }) => [
          styles.play,
          isDark ? styles.playDark : styles.playLight,
          pressed && styles.pressed,
        ]}
      >
        {status.isBuffering ? (
          <ActivityIndicator size="small" color={isDark ? colors.white : colors.primary} />
        ) : (
          <Ionicons
            name={isPlaying ? 'pause' : 'play'}
            size={18}
            color={isDark ? colors.white : colors.primary}
            style={!isPlaying ? styles.playIcon : undefined}
          />
        )}
      </Pressable>

      <View style={styles.waveWrap}>
        <Waveform
          color={isDark ? colors.white : colors.primary}
          mutedColor={isDark ? 'rgba(255,255,255,0.4)' : '#B6D9D2'}
          progress={progress}
          height={27}
          barWidth={2.6}
        />
      </View>

      <Text style={[styles.time, isDark ? styles.timeDark : styles.timeLight]}>
        {formatDuration(current)} / {formatDuration(total)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  play: {
    width: 44,
    height: 44,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playLight: {
    backgroundColor: colors.primarySoft,
  },
  playDark: {
    backgroundColor: 'rgba(255,255,255,0.17)',
  },
  playIcon: {
    marginLeft: 2,
  },
  pressed: {
    opacity: 0.7,
  },
  waveWrap: {
    flex: 1,
  },
  time: {
    fontFamily: fonts.bold,
    fontSize: 10.5,
    minWidth: 72,
    textAlign: 'right',
  },
  timeLight: {
    color: colors.inkSoft,
  },
  timeDark: {
    color: 'rgba(255,255,255,0.72)',
  },
});
