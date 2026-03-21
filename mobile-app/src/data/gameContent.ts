import { BuildingDefinition, DepartmentDefinition } from '../types/game';

export const gridSize = 5;

export const monthLabels = [
  '1월',
  '2월',
  '3월',
  '4월',
  '5월',
  '6월',
  '7월',
  '8월',
  '9월',
  '10월',
  '11월',
  '12월',
] as const;

export const buildingDefinitions: BuildingDefinition[] = [
  {
    id: 'classroom',
    name: '강의실',
    icon: '🏫',
    cost: 120,
    description: '학생 수용량과 교육력을 올립니다.',
  },
  {
    id: 'dormitory',
    name: '기숙사',
    icon: '🏠',
    cost: 140,
    description: '입학생 수를 늘리는 기숙사 수용량을 제공합니다.',
  },
  {
    id: 'laboratory',
    name: '연구소',
    icon: '🔬',
    cost: 180,
    description: '연구력과 분야 명성 성장을 돕습니다.',
  },
  {
    id: 'cafeteria',
    name: '식당',
    icon: '🍽️',
    cost: 90,
    description: '학생 유지율을 높여 안정적인 운영을 돕습니다.',
  },
];

export const departmentDefinitions: DepartmentDefinition[] = [
  {
    id: 'art',
    name: '미술학과',
    field: 'arts',
    cost: 120,
    capacity: 35,
    educationBoost: 4,
  },
  {
    id: 'computer',
    name: '컴퓨터공학과',
    field: 'engineering',
    cost: 150,
    capacity: 45,
    educationBoost: 5,
  },
  {
    id: 'medical',
    name: '의학과',
    field: 'medical',
    cost: 180,
    capacity: 30,
    educationBoost: 6,
  },
  {
    id: 'humanities',
    name: '인문학과',
    field: 'humanities',
    cost: 100,
    capacity: 40,
    educationBoost: 4,
  },
];
