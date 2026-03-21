export type ReputationField = 'arts' | 'engineering' | 'medical' | 'humanities';

export type BuildingType = 'classroom' | 'dormitory' | 'laboratory' | 'cafeteria';

export type DepartmentId = 'art' | 'computer' | 'medical' | 'humanities';

export type AdmissionCriteria = {
  math: number;
  science: number;
  english: number;
  korean: number;
};

export type BuildingDefinition = {
  id: BuildingType;
  name: string;
  icon: string;
  cost: number;
  description: string;
};

export type DepartmentDefinition = {
  id: DepartmentId;
  name: string;
  field: ReputationField;
  cost: number;
  capacity: number;
  educationBoost: number;
};

export type BuildingInstance = {
  id: string;
  type: BuildingType;
  row: number;
  col: number;
};

export type Tile = {
  row: number;
  col: number;
};

export type GameState = {
  year: number;
  month: number;
  budget: number;
  buildings: BuildingInstance[];
  departments: DepartmentId[];
  reputation: Record<ReputationField, number>;
  admissionCriteria: AdmissionCriteria;
  enrolledStudents: number;
  averageStudentLevel: number;
  logs: string[];
  hasSeenOnboarding: boolean;
};

export type DerivedStats = {
  educationPower: number;
  researchPower: number;
  dormCapacity: number;
  studentCapacity: number;
  totalReputation: number;
};
