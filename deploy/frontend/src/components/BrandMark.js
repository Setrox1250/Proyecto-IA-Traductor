import { StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

import { colors } from '../theme';

export default function BrandMark({ size = 42 }) {
  return (
    <LinearGradient
      colors={['#16766A', '#073E38']}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[
        styles.mark,
        { width: size, height: size, borderRadius: size * 0.34 },
      ]}
    >
      <Ionicons name="chatbubble-ellipses" size={size * 0.5} color={colors.white} />
      <View style={[styles.dot, { width: size * 0.2, height: size * 0.2 }]} />
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  mark: {
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.primaryDeep,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.22,
    shadowRadius: 12,
    elevation: 5,
  },
  dot: {
    position: 'absolute',
    right: 7,
    top: 7,
    borderRadius: 99,
    backgroundColor: colors.accent,
    borderWidth: 2,
    borderColor: '#0B5148',
  },
});
