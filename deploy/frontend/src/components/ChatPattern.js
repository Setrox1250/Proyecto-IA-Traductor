import { StyleSheet, View } from 'react-native';

import { colors } from '../theme';

export default function ChatPattern() {
  return (
    <View pointerEvents="none" style={StyleSheet.absoluteFill}>
      <View style={styles.grid}>
        {Array.from({ length: 240 }).map((_, index) => (
          <View key={index} style={styles.dot} />
        ))}
      </View>
      <View style={styles.washTop} />
      <View style={styles.washBottom} />
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    ...StyleSheet.absoluteFillObject,
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignContent: 'flex-start',
    gap: 24,
    paddingHorizontal: 14,
    paddingTop: 12,
    opacity: 0.75,
  },
  dot: {
    width: 2.5,
    height: 2.5,
    borderRadius: 2,
    backgroundColor: colors.primary,
    opacity: 0.07,
  },
  washTop: {
    position: 'absolute',
    top: -80,
    right: -70,
    width: 230,
    height: 230,
    borderRadius: 115,
    backgroundColor: 'rgba(244,161,92,0.055)',
  },
  washBottom: {
    position: 'absolute',
    bottom: -120,
    left: -80,
    width: 270,
    height: 270,
    borderRadius: 135,
    backgroundColor: 'rgba(103,93,224,0.045)',
  },
});
