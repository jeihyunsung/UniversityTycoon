import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { CampusTile } from '../components/CampusTile';
import { InfoCard } from '../components/InfoCard';
import { OnboardingCard } from '../components/OnboardingCard';
import { buildingDefinitions, departmentDefinitions, gridSize } from '../data/gameContent';
import { usePersistentGameState } from '../hooks/usePersistentGameState';
import { palette } from '../theme/palette';
import { DepartmentId, GameState, Tile } from '../types/game';
import {
  addBuilding,
  advanceMonth,
  getDerivedStats,
  getMonthLabel,
  getSeasonByMonth,
  getTileBuilding,
  openDepartment,
  updateAdmissionCriteria,
} from '../utils/gameLogic';

const seasonBackground = {
  spring: palette.spring,
  summer: palette.summer,
  autumn: palette.autumn,
  winter: palette.winter,
};

export function GameScreen() {
  const { gameState, setGameState, isHydrating, loadError, resetGame } = usePersistentGameState();
  const [selectedTile, setSelectedTile] = useState<Tile | null>(null);
  const [showDepartmentModal, setShowDepartmentModal] = useState(false);
  const [showAdmissionModal, setShowAdmissionModal] = useState(false);

  const stats = useMemo(() => getDerivedStats(gameState), [gameState]);
  const season = getSeasonByMonth(gameState.month);

  const nextTurn = () => {
    setGameState((current) => advanceMonth(current));
  };

  const onBuild = (buildingType: (typeof buildingDefinitions)[number]['id']) => {
    if (!selectedTile) {
      return;
    }

    setGameState((current) => addBuilding(current, selectedTile, buildingType));
    setSelectedTile(null);
  };

  const onOpenDepartment = (departmentId: DepartmentId) => {
    setGameState((current) => openDepartment(current, departmentId));
  };

  const adjustAdmission = (subject: keyof GameState['admissionCriteria'], delta: number) => {
    const nextValue = Math.min(9, Math.max(1, gameState.admissionCriteria[subject] + delta));
    setGameState((current) =>
      updateAdmissionCriteria(current, {
        ...current.admissionCriteria,
        [subject]: nextValue,
      }),
    );
  };

  const dismissOnboarding = () => {
    setGameState((current) => ({
      ...current,
      hasSeenOnboarding: true,
    }));
  };

  const confirmReset = () => {
    Alert.alert('새 게임 시작', '저장된 진행 상황을 지우고 처음부터 시작합니다.', [
      { text: '취소', style: 'cancel' },
      {
        text: '초기화',
        style: 'destructive',
        onPress: () => {
          void resetGame();
        },
      },
    ]);
  };

  if (isHydrating) {
    return (
      <View style={[styles.screen, styles.loadingScreen]}>
        <ActivityIndicator size="large" color={palette.coral} />
        <Text style={styles.loadingText}>캠퍼스를 불러오는 중입니다...</Text>
      </View>
    );
  }

  return (
    <View style={[styles.screen, { backgroundColor: seasonBackground[season] }]}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.heroCard}>
          <View>
            <Text style={styles.kicker}>University Tycoon</Text>
            <Text style={styles.heroTitle}>
              {gameState.year}년 {getMonthLabel(gameState.month)}
            </Text>
            <Text style={styles.heroSubtitle}>
              작은 대학을 귀여운 캠퍼스로 키우는 모바일 시뮬레이션 프로토타입
            </Text>
            {loadError ? <Text style={styles.warningText}>{loadError}</Text> : null}
          </View>
          <Pressable onPress={nextTurn} style={styles.primaryButton}>
            <Text style={styles.primaryButtonText}>다음 달로 진행</Text>
          </Pressable>
        </View>

        <View style={styles.cardGrid}>
          <InfoCard title="예산" accent={palette.butter}>
            <Text style={styles.bigValue}>{gameState.budget} G</Text>
            <Text style={styles.helperText}>등록금과 유지비를 반영한 현재 운영 자금</Text>
          </InfoCard>
          <InfoCard title="총 명성" accent={palette.peach}>
            <Text style={styles.bigValue}>{stats.totalReputation}</Text>
            <Text style={styles.helperText}>졸업 결과와 학과 개설로 성장합니다</Text>
          </InfoCard>
        </View>

        <View style={styles.cardGrid}>
          <InfoCard title="학생 현황" accent={palette.mint}>
            <Text style={styles.statLine}>재학생 {gameState.enrolledStudents}명</Text>
            <Text style={styles.statLine}>평균 수준 {gameState.averageStudentLevel}</Text>
            <Text style={styles.helperText}>수용량 {stats.studentCapacity} / 기숙사 {stats.dormCapacity}</Text>
          </InfoCard>
          <InfoCard title="운영 능력" accent={palette.lavender}>
            <Text style={styles.statLine}>교육력 {stats.educationPower}</Text>
            <Text style={styles.statLine}>연구력 {stats.researchPower}</Text>
            <Text style={styles.helperText}>강의실과 연구소, 학과가 영향을 줍니다</Text>
          </InfoCard>
        </View>

        <View style={styles.reputationRow}>
          <ReputationPill label="예체능" value={gameState.reputation.arts} color={palette.arts} />
          <ReputationPill label="공학" value={gameState.reputation.engineering} color={palette.engineering} />
          <ReputationPill label="의학" value={gameState.reputation.medical} color={palette.medical} />
          <ReputationPill label="기초학문" value={gameState.reputation.humanities} color={palette.humanities} />
        </View>

        <View style={styles.actionRow}>
          <SecondaryButton label="학과 개설" onPress={() => setShowDepartmentModal(true)} />
          <SecondaryButton label="입학 기준" onPress={() => setShowAdmissionModal(true)} />
        </View>

        <View style={styles.utilityRow}>
          <Pressable onPress={confirmReset} style={styles.ghostButton}>
            <Text style={styles.ghostButtonText}>새 게임 시작</Text>
          </Pressable>
          <Text style={styles.utilityHint}>진행 상황은 자동 저장됩니다.</Text>
        </View>

        <View style={styles.mapCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>캠퍼스 맵</Text>
            <Text style={styles.sectionSubtext}>빈 칸을 눌러 건물을 건설하세요</Text>
          </View>

          <View style={styles.grid}>
            {Array.from({ length: gridSize * gridSize }, (_, index) => {
              const row = Math.floor(index / gridSize);
              const col = index % gridSize;
              const building = getTileBuilding(gameState.buildings, { row, col });

              return (
                <CampusTile
                  key={`${row}-${col}`}
                  building={building}
                  onPress={() => setSelectedTile({ row, col })}
                />
              );
            })}
          </View>
        </View>

        <View style={styles.panelCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>이번 캠퍼스 로그</Text>
            <Text style={styles.sectionSubtext}>입학, 졸업, 운영 변화가 여기에 기록됩니다</Text>
          </View>
          {gameState.logs.map((log, index) => (
            <Text key={`${log}-${index}`} style={styles.logLine}>
              • {log}
            </Text>
          ))}
        </View>
      </ScrollView>

      <Modal transparent visible={selectedTile !== null} animationType="slide" onRequestClose={() => setSelectedTile(null)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>건물 건설</Text>
            <Text style={styles.modalSubtitle}>귀여운 캠퍼스 타일에 어떤 건물을 올릴까요?</Text>
            {selectedTile && getTileBuilding(gameState.buildings, selectedTile) ? (
              <>
                <Text style={styles.modalMessage}>이미 건물이 있는 자리입니다. 다른 칸을 선택하세요.</Text>
                <SecondaryButton label="닫기" onPress={() => setSelectedTile(null)} />
              </>
            ) : (
              <>
                {buildingDefinitions.map((building) => (
                  <Pressable key={building.id} onPress={() => onBuild(building.id)} style={styles.optionCard}>
                    <Text style={styles.optionTitle}>
                      {building.icon} {building.name} · {building.cost} G
                    </Text>
                    <Text style={styles.optionDescription}>{building.description}</Text>
                  </Pressable>
                ))}
                <SecondaryButton label="취소" onPress={() => setSelectedTile(null)} />
              </>
            )}
          </View>
        </View>
      </Modal>

      <Modal transparent visible={showDepartmentModal} animationType="slide" onRequestClose={() => setShowDepartmentModal(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>학과 개설</Text>
            <Text style={styles.modalSubtitle}>대학의 주력 분야를 하나씩 확장하세요.</Text>
            {departmentDefinitions.map((department) => {
              const opened = gameState.departments.includes(department.id);

              return (
                <Pressable
                  key={department.id}
                  onPress={() => onOpenDepartment(department.id)}
                  style={[styles.optionCard, opened && styles.disabledCard]}
                  disabled={opened}
                >
                  <Text style={styles.optionTitle}>
                    {department.name} · {department.cost} G
                  </Text>
                  <Text style={styles.optionDescription}>
                    수용량 {department.capacity} / 교육력 +{department.educationBoost}
                  </Text>
                  <Text style={styles.optionFootnote}>{opened ? '이미 개설됨' : '개설 시 해당 분야 명성 +4'}</Text>
                </Pressable>
              );
            })}
            <SecondaryButton label="닫기" onPress={() => setShowDepartmentModal(false)} />
          </View>
        </View>
      </Modal>

      <Modal transparent visible={showAdmissionModal} animationType="slide" onRequestClose={() => setShowAdmissionModal(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>입학 기준 설정</Text>
            <Text style={styles.modalSubtitle}>등급이 낮을수록 더 엄격한 기준입니다.</Text>
            {Object.entries(gameState.admissionCriteria).map(([subject, value]) => (
              <View key={subject} style={styles.criteriaRow}>
                <Text style={styles.criteriaLabel}>{subjectLabel(subject as keyof GameState['admissionCriteria'])}</Text>
                <View style={styles.criteriaControls}>
                  <Pressable onPress={() => adjustAdmission(subject as keyof GameState['admissionCriteria'], -1)} style={styles.adjustButton}>
                    <Text style={styles.adjustButtonText}>-</Text>
                  </Pressable>
                  <Text style={styles.criteriaValue}>{value}등급</Text>
                  <Pressable onPress={() => adjustAdmission(subject as keyof GameState['admissionCriteria'], 1)} style={styles.adjustButton}>
                    <Text style={styles.adjustButtonText}>+</Text>
                  </Pressable>
                </View>
              </View>
            ))}
            <SecondaryButton label="닫기" onPress={() => setShowAdmissionModal(false)} />
          </View>
        </View>
      </Modal>

      {!gameState.hasSeenOnboarding ? <OnboardingCard onClose={dismissOnboarding} /> : null}
    </View>
  );
}

function ReputationPill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={[styles.pill, { backgroundColor: color }]}>
      <Text style={styles.pillLabel}>{label}</Text>
      <Text style={styles.pillValue}>{value}</Text>
    </View>
  );
}

function SecondaryButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={styles.secondaryButton}>
      <Text style={styles.secondaryButtonText}>{label}</Text>
    </Pressable>
  );
}

function subjectLabel(subject: keyof GameState['admissionCriteria']) {
  switch (subject) {
    case 'math':
      return '수학';
    case 'science':
      return '과학';
    case 'english':
      return '영어';
    case 'korean':
      return '국어';
  }
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  loadingScreen: {
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.sky,
    gap: 12,
  },
  loadingText: {
    fontSize: 15,
    fontWeight: '700',
    color: palette.navy,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  heroCard: {
    backgroundColor: palette.white,
    borderRadius: 28,
    padding: 20,
    borderWidth: 1,
    borderColor: palette.border,
    shadowColor: '#355070',
    shadowOpacity: 0.08,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 3,
    gap: 14,
  },
  kicker: {
    fontSize: 13,
    fontWeight: '700',
    color: palette.coral,
    marginBottom: 6,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: palette.navy,
  },
  heroSubtitle: {
    marginTop: 8,
    fontSize: 15,
    lineHeight: 22,
    color: palette.slate,
  },
  warningText: {
    marginTop: 10,
    fontSize: 13,
    lineHeight: 18,
    color: palette.danger,
  },
  primaryButton: {
    backgroundColor: palette.coral,
    borderRadius: 18,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: palette.white,
    fontSize: 15,
    fontWeight: '800',
  },
  cardGrid: {
    flexDirection: 'row',
    gap: 12,
    flexWrap: 'wrap',
  },
  bigValue: {
    fontSize: 26,
    fontWeight: '800',
    color: palette.navy,
  },
  helperText: {
    marginTop: 6,
    fontSize: 13,
    lineHeight: 18,
    color: palette.slate,
  },
  statLine: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '700',
    color: palette.navy,
  },
  reputationRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  pill: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 999,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  pillLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: palette.navy,
  },
  pillValue: {
    fontSize: 13,
    fontWeight: '800',
    color: palette.navy,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
  },
  utilityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  utilityHint: {
    flex: 1,
    textAlign: 'right',
    fontSize: 13,
    color: palette.slate,
  },
  ghostButton: {
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: '#ffffffaa',
    borderWidth: 1,
    borderColor: palette.border,
  },
  ghostButtonText: {
    fontSize: 13,
    fontWeight: '800',
    color: palette.navy,
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: palette.white,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: palette.border,
    alignItems: 'center',
    paddingVertical: 14,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '800',
    color: palette.navy,
  },
  mapCard: {
    backgroundColor: '#c8e6f4',
    borderRadius: 28,
    padding: 18,
    gap: 14,
  },
  panelCard: {
    backgroundColor: palette.white,
    borderRadius: 28,
    padding: 18,
    borderWidth: 1,
    borderColor: palette.border,
    gap: 10,
  },
  sectionHeader: {
    gap: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: palette.navy,
  },
  sectionSubtext: {
    fontSize: 13,
    color: palette.slate,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    justifyContent: 'center',
  },
  logLine: {
    fontSize: 14,
    lineHeight: 22,
    color: palette.navy,
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: '#20304055',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: palette.white,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 20,
    gap: 12,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: palette.navy,
  },
  modalSubtitle: {
    fontSize: 14,
    lineHeight: 20,
    color: palette.slate,
    marginBottom: 4,
  },
  modalMessage: {
    fontSize: 15,
    lineHeight: 22,
    color: palette.navy,
    marginBottom: 8,
  },
  optionCard: {
    padding: 14,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: palette.border,
    backgroundColor: palette.cream,
    gap: 4,
  },
  disabledCard: {
    opacity: 0.45,
  },
  optionTitle: {
    fontSize: 15,
    fontWeight: '800',
    color: palette.navy,
  },
  optionDescription: {
    fontSize: 13,
    lineHeight: 18,
    color: palette.slate,
  },
  optionFootnote: {
    marginTop: 2,
    fontSize: 12,
    color: palette.slate,
  },
  criteriaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  criteriaLabel: {
    fontSize: 15,
    fontWeight: '700',
    color: palette.navy,
  },
  criteriaControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  criteriaValue: {
    minWidth: 52,
    textAlign: 'center',
    fontSize: 15,
    fontWeight: '800',
    color: palette.navy,
  },
  adjustButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: palette.lavender,
    alignItems: 'center',
    justifyContent: 'center',
  },
  adjustButtonText: {
    fontSize: 18,
    fontWeight: '800',
    color: palette.navy,
  },
});
