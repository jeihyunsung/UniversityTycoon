# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

University Tycoon is a university management simulation game powered by a Kakao chatbot skill server.
- **chatbot-server/**: Python FastAPI backend (Kakao chatbot skill server)

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

## Architecture

```
Kakao webhook POST → routes/kakao.py (9 endpoints under /webhooks/kakao)
  → GameEngine (services/game_engine.py) — core game logic, singleton instance
  → InMemorySaveRepository (repositories/in_memory.py) — dict-based, no persistence across restarts
  → KakaoAdapter (services/kakao_adapter.py) — formats responses for Kakao
```

- **schemas.py**: Pydantic models — `SaveState` (full game state), `KakaoWebhookRequest`, `GameResult`. Uses `Literal` types for `BuildingType`, `DepartmentId`, `AdmissionPolicy`.
- **game_engine.py**: Frozen dataclasses for `BuildingDefinition`/`DepartmentDefinition`. Constants `BUILDINGS`, `DEPARTMENTS`. Methods: `start_game`, `advance_turn`, `build`, `department`, `admission`, `load_status`.
- Persistence is in-memory only (planned: PostgreSQL + SQLAlchemy).

### Game Mechanics (key constants for balance work)

- **Budget**: Start 480G. Income = students × 3.2/mo. Costs = buildings × 18 + departments × 14/mo.
- **Students**: Start 72. February: graduation (~24% leave). March: admission (capacity + dorms + policy).
- **Admission policies**: "easy", "normal", "hard" — affect student intake.
- **Reputation**: 4 fields (arts, engineering, medical, humanities). Affected by departments and graduation.

## Documentation

Design docs are in the repo root (Korean): `university_sim_game_design.md`, `kakao_skill_server_api_spec.md`, `kakao_chatbot_game_design.md`.
