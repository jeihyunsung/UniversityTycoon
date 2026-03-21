import { Pressable, StyleSheet, Text } from 'react-native';

import { palette } from '../theme/palette';
import { BuildingInstance } from '../types/game';

type CampusTileProps = {
  building: BuildingInstance | null;
  onPress: () => void;
};

const iconByType = {
  classroom: '🏫',
  dormitory: '🏠',
  laboratory: '🔬',
  cafeteria: '🍽️',
};

export function CampusTile({ building, onPress }: CampusTileProps) {
  return (
    <Pressable onPress={onPress} style={[styles.tile, building ? styles.occupiedTile : styles.emptyTile]}>
      <Text style={styles.icon}>{building ? iconByType[building.type] : '🌱'}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tile: {
    width: 54,
    height: 54,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#ffffffcc',
  },
  emptyTile: {
    backgroundColor: '#ffffff99',
  },
  occupiedTile: {
    backgroundColor: '#fff8ef',
  },
  icon: {
    fontSize: 24,
  },
});
