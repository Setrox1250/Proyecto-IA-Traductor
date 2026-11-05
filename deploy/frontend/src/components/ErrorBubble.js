import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { colors, fonts, shadows } from '../theme';

export default function ErrorBubble({ message, onRetry, requestId }) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.icon}>
          <Ionicons name="alert-circle-outline" size={18} color={colors.danger} />
        </View>
        <View style={styles.headerText}>
          <Text style={styles.title}>No pudimos completar la traducción</Text>
          <Text style={styles.description}>{message}</Text>
        </View>
      </View>

      {requestId ? (
        <Text style={styles.requestId}>Referencia: {requestId}</Text>
      ) : null}

      {onRetry ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Reintentar procesamiento"
          onPress={onRetry}
          style={({ pressed }) => [styles.retry, pressed && styles.pressed]}
        >
          <Ionicons name="refresh" size={14} color={colors.danger} />
          <Text style={styles.retryText}>Reintentar</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    maxWidth: 560,
    backgroundColor: '#FFF8F6',
    borderRadius: 20,
    borderTopLeftRadius: 7,
    borderWidth: 1,
    borderColor: '#F4D8D1',
    padding: 14,
    ...shadows.soft,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
  },
  icon: {
    width: 34,
    height: 34,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FDEAE6',
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontFamily: fonts.extrabold,
    fontSize: 14,
    color: colors.ink,
    marginBottom: 3,
  },
  description: {
    fontFamily: fonts.medium,
    fontSize: 12,
    lineHeight: 18,
    color: colors.inkSoft,
  },
  requestId: {
    fontFamily: fonts.medium,
    fontSize: 9.5,
    color: colors.inkFaint,
    marginTop: 8,
  },
  retry: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 6,
    backgroundColor: '#FDEAE6',
    marginTop: 10,
  },
  retryText: {
    fontFamily: fonts.bold,
    fontSize: 10.5,
    color: colors.danger,
  },
  pressed: {
    opacity: 0.7,
  },
});
