import { Pressable, StyleSheet, Text, View } from 'react-native';

import { palette } from '../theme/palette';

type OnboardingCardProps = {
  onClose: () => void;
};

export function OnboardingCard({ onClose }: OnboardingCardProps) {
  return (
    <View style={styles.overlay}>
      <View style={styles.card}>
        <Text style={styles.kicker}>첫 플레이 안내</Text>
        <Text style={styles.title}>작은 대학을 1년씩 굴려 보세요</Text>
        <Text style={styles.body}>
          `다음 달로 진행`으로 시간이 흐르고, 빈 타일에는 건물을 지을 수 있습니다. 10월에는 입학 기준을 조정하고, 2월과 3월에는 졸업과 입학 결과가 자동으로 반영됩니다.
        </Text>
        <View style={styles.tipBox}>
          <Text style={styles.tipTitle}>처음 추천 루트</Text>
          <Text style={styles.tipText}>1. 강의실을 1개 더 짓기</Text>
          <Text style={styles.tipText}>2. 컴퓨터공학과 개설하기</Text>
          <Text style={styles.tipText}>3. 예산이 안정되면 연구소 추가하기</Text>
        </View>
        <Pressable onPress={onClose} style={styles.button}>
          <Text style={styles.buttonText}>시작하기</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#20304066',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    maxWidth: 420,
    backgroundColor: palette.white,
    borderRadius: 28,
    padding: 22,
    borderWidth: 1,
    borderColor: palette.border,
    gap: 12,
  },
  kicker: {
    fontSize: 13,
    fontWeight: '700',
    color: palette.coral,
  },
  title: {
    fontSize: 24,
    lineHeight: 30,
    fontWeight: '800',
    color: palette.navy,
  },
  body: {
    fontSize: 15,
    lineHeight: 22,
    color: palette.slate,
  },
  tipBox: {
    padding: 14,
    borderRadius: 20,
    backgroundColor: palette.cream,
    gap: 6,
  },
  tipTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: palette.navy,
  },
  tipText: {
    fontSize: 14,
    color: palette.slate,
  },
  button: {
    marginTop: 4,
    backgroundColor: palette.coral,
    borderRadius: 18,
    paddingVertical: 14,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 15,
    fontWeight: '800',
    color: palette.white,
  },
});
