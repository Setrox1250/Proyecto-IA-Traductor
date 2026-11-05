import { StyleSheet, View } from 'react-native';

const HEIGHTS = [8, 15, 11, 20, 13, 24, 9, 17, 12, 22, 8, 16, 20, 11, 15, 9, 13, 19, 10, 14, 21, 9, 16, 12];

export default function Waveform({
  color = '#FFFFFF',
  mutedColor,
  height = 26,
  barWidth = 3,
  activeBars = 0,
  progress = null,
}) {
  const total = HEIGHTS.length;
  return (
    <View style={[styles.row, { height }]}>
      {HEIGHTS.map((value, index) => {
        const active =
          progress === null
            ? index < activeBars
            : index / total < Math.min(Math.max(progress, 0), 1);
        return (
          <View
            key={`${value}-${index}`}
            style={{
              width: barWidth,
              height: Math.min(value, height),
              borderRadius: 99,
              backgroundColor: active ? color : mutedColor || color,
              opacity: active ? 1 : mutedColor ? 0.72 : 0.4,
            }}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2.5,
    flex: 1,
    overflow: 'hidden',
  },
});
