# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

University Tycoon is a university management simulation game with two components:
- **chatbot-server/**: Python FastAPI backend (Kakao chatbot skill server)
- **mobile-app/**: React Native (Expo) mobile frontend

The game involves managing budget, buildings, departments, students, and reputation across monthly turns.

## Commands

### Backend (chatbot-server/)
```bash
cd chatbot-server
pip install -e .                    # Install dependencies
uvicorn app.main:app --reload       # Run dev server (port 8000)
curl http://127.0.0.1:8000/health   # Health check
```

Dependencies: FastAPI, Uvicorn, Pydantic. Python 3.11+.

No test suite or linter configured yet. Use `pytest` for new tests and `ruff` for linting.

### Frontend (mobile-app/)
```bash
cd mobile-app
npm install                         # Install dependencies
npx expo start --clear              # Run with Expo (iOS via Expo Go)
```

Stack: Expo ~54, React 19, React Native 0.81, TypeScript ~5.9.

## Architecture

### Backend

```
Kakao webhook POST → routes/kakao.py (9 endpoints under /webhooks/kakao)
  → GameEngine (services/game_engine.py) — core game logic, singleton instance
  → InMemorySaveRepository (repositories/in_memory.py) — dict-based, no persistence across restarts
  → KakaoAdapter (services/kakao_adapter.py) — formats responses for Kakao
```

- **schemas.py**: Pydantic models — `SaveState` (full game state), `KakaoWebhookRequest`, `GameResult`. Uses `Literal` types for `BuildingType`, `DepartmentId`, `AdmissionPolicy`.
- **game_engine.py**: Frozen dataclasses for `BuildingDefinition`/`DepartmentDefinition`. Constants `BUILDINGS`, `DEPARTMENTS`. Methods: `start_game`, `advance_turn`, `build`, `department`, `admission`, `load_status`.
- Persistence is in-memory only (planned: PostgreSQL + SQLAlchemy).

### Frontend

```
GameScreen (main UI, manages modals and layout)
  → usePersistentGameState hook (AsyncStorage load/save)
  → gameLogic.ts (pure functions: createInitialState, addBuilding, openDepartment, advanceMonth)
  → gameContent.ts (building/department definitions, 5×5 grid)
  → Components: CampusTile (grid tile), InfoCard (stats), OnboardingCard (tutorial)
```

- State: local `useState` + AsyncStorage auto-save on every change.
- `getDerivedStats()` computes education/research power, capacity, reputation.
- Season system: month determines background color (Spring/Summer/Autumn/Winter).

### Game Mechanics (key constants for balance work)

- **Budget**: Start 480G. Income = students × 3.2/mo. Costs = buildings × 18 + departments × 14/mo.
- **Students**: Start 72. February: graduation (~24% leave). March: admission (capacity + dorms + policy).
- **Admission policies**: "easy", "normal", "hard" — affect student intake.
- **Reputation**: 4 fields (arts, engineering, medical, humanities). Affected by departments and graduation.

## Documentation

Design docs are in the repo root (Korean): `university_sim_game_design.md`, `university_sim_mvp_plan.md`, `kakao_skill_server_api_spec.md`, `kakao_chatbot_game_design.md`, `ui_style_guide.md`.

## Dual Codebase

Backend and frontend have **parallel but independent** game logic implementations. Changes to game mechanics must be updated in both `chatbot-server/app/services/game_engine.py` and `mobile-app/src/utils/gameLogic.ts` to stay in sync.
