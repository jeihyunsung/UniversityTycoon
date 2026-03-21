import { buildingDefinitions, departmentDefinitions, monthLabels } from '../data/gameContent';
import {
  BuildingInstance,
  BuildingType,
  DepartmentId,
  DerivedStats,
  GameState,
  ReputationField,
  Tile,
} from '../types/game';

const buildingLookup = Object.fromEntries(buildingDefinitions.map((item) => [item.id, item]));
const departmentLookup = Object.fromEntries(departmentDefinitions.map((item) => [item.id, item]));

export function createInitialState(): GameState {
  return {
    year: 1,
    month: 1,
    budget: 480,
    buildings: [
      { id: 'starter-classroom', type: 'classroom', row: 2, col: 2 },
      { id: 'starter-dormitory', type: 'dormitory', row: 3, col: 1 },
    ],
    departments: ['humanities'],
    reputation: {
      arts: 6,
      engineering: 6,
      medical: 6,
      humanities: 12,
    },
    admissionCriteria: {
      math: 5,
      science: 5,
      english: 5,
      korean: 5,
    },
    enrolledStudents: 72,
    averageStudentLevel: 5,
    logs: ['작은 캠퍼스로 새로운 학기를 시작했습니다.'],
    hasSeenOnboarding: false,
  };
}

export function getDerivedStats(state: GameState): DerivedStats {
  const classroomCount = countBuildings(state.buildings, 'classroom');
  const dormitoryCount = countBuildings(state.buildings, 'dormitory');
  const laboratoryCount = countBuildings(state.buildings, 'laboratory');
  const cafeteriaCount = countBuildings(state.buildings, 'cafeteria');

  const departmentStats = state.departments.reduce(
    (accumulator, departmentId) => {
      const department = departmentLookup[departmentId];
      accumulator.educationBoost += department.educationBoost;
      accumulator.capacity += department.capacity;
      return accumulator;
    },
    { educationBoost: 0, capacity: 0 },
  );

  return {
    educationPower: classroomCount * 8 + departmentStats.educationBoost + cafeteriaCount * 2,
    researchPower: laboratoryCount * 10 + state.departments.length * 2,
    dormCapacity: dormitoryCount * 40,
    studentCapacity: classroomCount * 60 + departmentStats.capacity,
    totalReputation:
      state.reputation.arts +
      state.reputation.engineering +
      state.reputation.medical +
      state.reputation.humanities,
  };
}

export function getSeasonByMonth(month: number) {
  if (month >= 3 && month <= 5) {
    return 'spring';
  }

  if (month >= 6 && month <= 8) {
    return 'summer';
  }

  if (month >= 9 && month <= 11) {
    return 'autumn';
  }

  return 'winter';
}

export function getMonthLabel(month: number) {
  return monthLabels[month - 1];
}

export function getTileBuilding(buildings: BuildingInstance[], tile: Tile) {
  return buildings.find((building) => building.row === tile.row && building.col === tile.col) ?? null;
}

export function canBuildOnTile(buildings: BuildingInstance[], tile: Tile) {
  return !getTileBuilding(buildings, tile);
}

export function addBuilding(state: GameState, tile: Tile, type: BuildingType): GameState {
  const definition = buildingLookup[type];

  if (!canBuildOnTile(state.buildings, tile) || state.budget < definition.cost) {
    return state;
  }

  return {
    ...state,
    budget: state.budget - definition.cost,
    buildings: [
      ...state.buildings,
      {
        id: `${type}-${tile.row}-${tile.col}-${state.buildings.length + 1}`,
        type,
        row: tile.row,
        col: tile.col,
      },
    ],
    logs: [
      `${definition.name}을(를) 건설했습니다. 캠퍼스가 조금 더 북적이기 시작합니다.`,
      ...state.logs,
    ].slice(0, 8),
  };
}

export function openDepartment(state: GameState, departmentId: DepartmentId): GameState {
  const definition = departmentLookup[departmentId];

  if (state.departments.includes(departmentId) || state.budget < definition.cost) {
    return state;
  }

  return {
    ...state,
    budget: state.budget - definition.cost,
    departments: [...state.departments, departmentId],
    reputation: {
      ...state.reputation,
      [definition.field]: state.reputation[definition.field] + 4,
    },
    logs: [`${definition.name}를 개설했습니다. 지원자들의 관심이 늘어납니다.`, ...state.logs].slice(0, 8),
  };
}

export function updateAdmissionCriteria(state: GameState, nextCriteria: GameState['admissionCriteria']): GameState {
  return {
    ...state,
    admissionCriteria: nextCriteria,
    logs: ['입학 기준을 새로 정했습니다. 10월 입시 전략이 반영됩니다.', ...state.logs].slice(0, 8),
  };
}

export function advanceMonth(state: GameState): GameState {
  const nextMonth = state.month === 12 ? 1 : state.month + 1;
  const nextYear = state.month === 12 ? state.year + 1 : state.year;
  const baseState = {
    ...state,
    month: nextMonth,
    year: nextYear,
  };

  const monthlyState = applyMonthlyBudget(baseState);
  const eventState = applyScheduledEvents(monthlyState);

  return {
    ...eventState,
    logs: [
      `${eventState.year}년 ${getMonthLabel(eventState.month)} 일정이 시작됐습니다.`,
      ...eventState.logs,
    ].slice(0, 8),
  };
}

function applyMonthlyBudget(state: GameState): GameState {
  const stats = getDerivedStats(state);
  const monthlyIncome = Math.floor(state.enrolledStudents * 3.2);
  const maintenance = state.buildings.length * 18 + state.departments.length * 14;
  const budgetDelta = monthlyIncome - maintenance;

  return {
    ...state,
    budget: Math.max(0, state.budget + budgetDelta),
    logs: [
      `이번 달 운영 결과: 등록금 ${monthlyIncome}, 유지비 ${maintenance}, 순변화 ${budgetDelta}.`,
      ...state.logs,
    ].slice(0, 8),
  };
}

function applyScheduledEvents(state: GameState): GameState {
  let nextState = state;

  if (state.month === 2) {
    nextState = applyGraduation(nextState);
  }

  if (state.month === 3) {
    nextState = applyAdmission(nextState);
  }

  if (state.month === 10) {
    nextState = {
      ...nextState,
      logs: ['10월입니다. 입학 기준을 점검할 시기입니다.', ...nextState.logs].slice(0, 8),
    };
  }

  return nextState;
}

function applyAdmission(state: GameState): GameState {
  const stats = getDerivedStats(state);
  const criteriaAverage = average(Object.values(state.admissionCriteria));
  const difficultyPenalty = Math.round(criteriaAverage * 7);
  const freshmen = Math.max(20, 110 - difficultyPenalty + Math.round(stats.dormCapacity * 0.35));
  const nextEnrolled = Math.min(stats.studentCapacity, freshmen + Math.floor(state.enrolledStudents * 0.75));
  const nextLevel = Math.max(1, 10 - criteriaAverage);

  return {
    ...state,
    enrolledStudents: nextEnrolled,
    averageStudentLevel: Number(nextLevel.toFixed(1)),
    logs: [
      `신입생 ${freshmen}명이 지원했고, 현재 재학생은 ${nextEnrolled}명입니다.`,
      ...state.logs,
    ].slice(0, 8),
  };
}

function applyGraduation(state: GameState): GameState {
  const stats = getDerivedStats(state);
  const graduateCount = Math.max(18, Math.floor(state.enrolledStudents * 0.24));
  const score = state.averageStudentLevel + stats.educationPower * 0.2 + stats.researchPower * 0.12;

  const professor = Math.floor(graduateCount * clamp(score / 180, 0.04, 0.12));
  const startup = Math.floor(graduateCount * clamp(score / 120, 0.06, 0.16));
  const enterprise = Math.floor(graduateCount * clamp(score / 80, 0.18, 0.32));
  const general = Math.max(0, graduateCount - professor - startup - enterprise);
  const gainedReputation = professor * 5 + startup * 10 + enterprise * 3 + general;
  const field = getLeadingField(state.reputation);

  return {
    ...state,
    enrolledStudents: Math.max(20, state.enrolledStudents - graduateCount),
    reputation: {
      ...state.reputation,
      [field]: state.reputation[field] + gainedReputation,
    },
    logs: [
      `졸업생 ${graduateCount}명 배출: 교수 ${professor}, 창업 ${startup}, 대기업 ${enterprise}, 일반 ${general}.`,
      `${fieldLabel(field)} 명성이 ${gainedReputation} 상승했습니다.`,
      ...state.logs,
    ].slice(0, 8),
  };
}

function countBuildings(buildings: BuildingInstance[], type: BuildingType) {
  return buildings.filter((building) => building.type === type).length;
}

function average(values: number[]) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function getLeadingField(reputation: Record<ReputationField, number>) {
  return (Object.entries(reputation).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'humanities') as ReputationField;
}

function fieldLabel(field: ReputationField) {
  switch (field) {
    case 'arts':
      return '예체능';
    case 'engineering':
      return '공학';
    case 'medical':
      return '의학';
    case 'humanities':
      return '기초학문';
  }
}
