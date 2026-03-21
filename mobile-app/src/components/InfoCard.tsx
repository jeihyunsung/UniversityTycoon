import { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { palette } from '../theme/palette';

type InfoCardProps = {
  title: string;
  accent: string;
  children: ReactNode;
};

export function InfoCard({ title, accent, children }: InfoCardProps) {
  return (
    <View style={styles.card}>
      <View style={[styles.badge, { backgroundColor: accent }]} />
      <Text style={styles.title}>{title}</Text>
      <View>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: 150,
    padding: 14,
    borderRadius: 20,
    backgroundColor: palette.white,
    borderWidth: 1,
    borderColor: palette.border,
    shadowColor: '#355070',
    shadowOpacity: 0.08,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 3,
    gap: 8,
  },
  badge: {
    width: 34,
    height: 8,
    borderRadius: 999,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: palette.slate,
  },
});
