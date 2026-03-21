import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useRef, useState } from 'react';

import { STORAGE_KEYS } from '../constants/storage';
import { GameState } from '../types/game';
import { createInitialState } from '../utils/gameLogic';

export function usePersistentGameState() {
  const [gameState, setGameState] = useState<GameState>(createInitialState);
  const [isHydrating, setIsHydrating] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function loadGame() {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEYS.gameState);
        const baseState = createInitialState();

        if (!raw) {
          if (!cancelled) {
            setGameState(baseState);
          }
          return;
        }

        const parsed = JSON.parse(raw) as Partial<GameState>;
        const mergedState: GameState = {
          ...baseState,
          ...parsed,
          reputation: {
            ...baseState.reputation,
            ...parsed.reputation,
          },
          admissionCriteria: {
            ...baseState.admissionCriteria,
            ...parsed.admissionCriteria,
          },
        };

        if (!cancelled) {
          setGameState(mergedState);
        }
      } catch {
        if (!cancelled) {
          setLoadError('저장 데이터를 읽지 못해 새 게임으로 시작했습니다.');
          setGameState(createInitialState());
        }
      } finally {
        if (!cancelled) {
          hasLoadedRef.current = true;
          setIsHydrating(false);
        }
      }
    }

    void loadGame();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!hasLoadedRef.current) {
      return;
    }

    void AsyncStorage.setItem(STORAGE_KEYS.gameState, JSON.stringify(gameState));
  }, [gameState]);

  const resetGame = async () => {
    await AsyncStorage.removeItem(STORAGE_KEYS.gameState);
    setGameState(createInitialState());
    setLoadError(null);
  };

  return {
    gameState,
    setGameState,
    isHydrating,
    loadError,
    resetGame,
  };
}
