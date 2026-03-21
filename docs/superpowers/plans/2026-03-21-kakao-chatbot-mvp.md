# Kakao Chatbot MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make University Tycoon playable via Kakao Talk chatbot — game logic unified with mobile app, PostgreSQL persistence, deployed to Render with HTTPS.

**Architecture:** FastAPI skill server receives Kakao Open Builder webhooks, runs game logic via `GameEngine`, persists to PostgreSQL via SQLAlchemy async. Response adapter converts `GameResult` to Kakao JSON format. Repository interface abstracts storage so in-memory and DB backends are interchangeable.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy (async) + asyncpg, PostgreSQL, Alembic, pytest, Render (PaaS)

---

## Parallel Execution Map

Tasks are designed for parallel dispatch where dependencies allow:

```
Phase 1 (parallel):
  Task 1: Repository interface + SQLAlchemy models
  Task 2: Unify game logic (graduation + admission)
  Task 3: pytest setup + GameEngine unit tests

Phase 2 (after Phase 1):
  Task 4: Wire async DB into FastAPI (depends on Task 1, 2, 3)
  Task 5: Integration tests for API endpoints (depends on Task 4)

Phase 3 (sequential):
  Task 6: Deploy to Render (depends on Task 5)
  Task 7: Kakao Open Builder wiring guide (depends on Task 6)
```

---

## File Structure

```
chatbot-server/
  pyproject.toml                          # MODIFY: add sqlalchemy, asyncpg, alembic, pytest deps
  alembic.ini                             # CREATE: alembic config
  alembic/
    env.py                                # CREATE: migration environment
    versions/
      001_initial_tables.py               # CREATE: users, game_saves, buildings, departments, turn_logs
  app/
    main.py                               # MODIFY: add lifespan for DB session engine
    config.py                             # CREATE: settings via pydantic-settings (DATABASE_URL etc.)
    models/
      schemas.py                          # MODIFY: add admission_criteria fields, graduation detail fields
      db_models.py                        # CREATE: SQLAlchemy ORM models
    repositories/
      base.py                             # CREATE: abstract SaveRepository interface
      in_memory.py                        # MODIFY: implement SaveRepository interface
      postgres.py                         # CREATE: PostgreSQL implementation of SaveRepository
    services/
      game_engine.py                      # MODIFY: unify graduation/admission logic with mobile app
      kakao_adapter.py                    # no changes needed
    api/
      routes/
        kakao.py                          # MODIFY: inject repository via Depends, async handlers
        health.py                         # MODIFY: add DB health check
      deps.py                             # CREATE: repository dependency injection
  tests/
    __init__.py                           # CREATE: empty package init
    conftest.py                           # CREATE: fixtures (fake request, in-memory repo, test engine)
    test_game_engine.py                   # CREATE: unit tests for GameEngine
    test_graduation.py                    # CREATE: graduation logic tests
    test_admission.py                     # CREATE: admission logic tests
    test_api.py                           # CREATE: FastAPI TestClient integration tests
  render.yaml                             # CREATE: Render deployment blueprint
  Dockerfile                              # CREATE: container for Render deploy
```

---

### Task 1: Repository Interface + SQLAlchemy DB Models

**Files:**
- Create: `chatbot-server/app/config.py`
- Create: `chatbot-server/app/models/db_models.py`
- Create: `chatbot-server/app/repositories/base.py`
- Modify: `chatbot-server/app/repositories/in_memory.py`
- Create: `chatbot-server/app/repositories/postgres.py`
- Modify: `chatbot-server/pyproject.toml`
- Create: `chatbot-server/alembic.ini`
- Create: `chatbot-server/alembic/env.py`
- Create: `chatbot-server/alembic/versions/001_initial_tables.py`

- [ ] **Step 1: Add dependencies to pyproject.toml**

Add to `dependencies` in `chatbot-server/pyproject.toml`:
```toml
dependencies = [
  "fastapi>=0.115,<1.0",
  "uvicorn[standard]>=0.30,<1.0",
  "pydantic>=2.8,<3.0",
  "pydantic-settings>=2.5,<3.0",
  "sqlalchemy[asyncio]>=2.0,<3.0",
  "asyncpg>=0.30,<1.0",
  "alembic>=1.14,<2.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.24",
  "httpx>=0.27",
  "aiosqlite>=0.20",
]
```

Run: `cd chatbot-server && pip install -e ".[dev]"`

- [ ] **Step 2: Create config.py**

```python
# chatbot-server/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    use_db: bool = False

    model_config = {"env_prefix": "UT_"}

    @property
    def async_database_url(self) -> str:
        """Auto-replace postgresql:// with postgresql+asyncpg:// for Render compatibility."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

settings = Settings()
```

- [ ] **Step 3: Create abstract repository interface**

```python
# chatbot-server/app/repositories/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from app.models.schemas import SaveState

class SaveRepository(ABC):
    @abstractmethod
    async def get(self, user_key: str) -> SaveState | None: ...

    @abstractmethod
    async def put(self, user_key: str, save: SaveState) -> SaveState: ...
```

- [ ] **Step 4: Update InMemorySaveRepository to implement interface**

```python
# chatbot-server/app/repositories/in_memory.py
from app.models.schemas import SaveState
from app.repositories.base import SaveRepository

class InMemorySaveRepository(SaveRepository):
    def __init__(self) -> None:
        self._saves: dict[str, SaveState] = {}

    async def get(self, user_key: str) -> SaveState | None:
        return self._saves.get(user_key)

    async def put(self, user_key: str, save: SaveState) -> SaveState:
        self._saves[user_key] = save
        return save

save_repository = InMemorySaveRepository()
```

- [ ] **Step 5: Create SQLAlchemy ORM models**

```python
# chatbot-server/app/models/db_models.py
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import JSON, DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class GameSaveRow(Base):
    __tablename__ = "game_saves"

    user_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, default=1)
    month: Mapped[int] = mapped_column(Integer, default=1)
    budget: Mapped[int] = mapped_column(Integer, default=480)
    reputation_arts: Mapped[int] = mapped_column(Integer, default=6)
    reputation_engineering: Mapped[int] = mapped_column(Integer, default=6)
    reputation_medical: Mapped[int] = mapped_column(Integer, default=6)
    reputation_humanities: Mapped[int] = mapped_column(Integer, default=12)
    enrolled_students: Mapped[int] = mapped_column(Integer, default=72)
    average_student_level: Mapped[float] = mapped_column(Float, default=5.0)
    admission_policy: Mapped[str] = mapped_column(String(16), default="normal")
    admission_criteria: Mapped[dict] = mapped_column(
        JSON, default=lambda: {"math": 5, "science": 5, "english": 5, "korean": 5}
    )
    buildings: Mapped[dict] = mapped_column(JSON, default=dict)
    departments: Mapped[list] = mapped_column(JSON, default=list)
    logs: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

- [ ] **Step 6: Create PostgreSQL repository**

```python
# chatbot-server/app/repositories/postgres.py
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db_models import GameSaveRow
from app.models.schemas import (
    AdmissionCriteria, BuildingState, ReputationState, SaveState, StudentState,
)
from app.repositories.base import SaveRepository

class PostgresSaveRepository(SaveRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_key: str) -> SaveState | None:
        row = await self._session.get(GameSaveRow, user_key)
        if row is None:
            return None
        return self._row_to_save(row)

    async def put(self, user_key: str, save: SaveState) -> SaveState:
        row = await self._session.get(GameSaveRow, user_key)
        if row is None:
            row = GameSaveRow(user_key=user_key)
            self._session.add(row)
        row.year = save.year
        row.month = save.month
        row.budget = save.budget
        row.reputation_arts = save.reputation.arts
        row.reputation_engineering = save.reputation.engineering
        row.reputation_medical = save.reputation.medical
        row.reputation_humanities = save.reputation.humanities
        row.enrolled_students = save.students.enrolled
        row.average_student_level = save.students.average_level
        row.admission_policy = save.admission_policy
        row.admission_criteria = {
            "math": save.admission_criteria.math,
            "science": save.admission_criteria.science,
            "english": save.admission_criteria.english,
            "korean": save.admission_criteria.korean,
        }
        row.buildings = {
            "classroom": save.buildings.classroom,
            "dormitory": save.buildings.dormitory,
            "laboratory": save.buildings.laboratory,
            "cafeteria": save.buildings.cafeteria,
        }
        row.departments = list(save.departments)
        row.logs = list(save.logs)
        await self._session.commit()
        return save

    def _row_to_save(self, row: GameSaveRow) -> SaveState:
        buildings = row.buildings or {}
        return SaveState(
            userId=row.user_key,
            year=row.year,
            month=row.month,
            budget=row.budget,
            reputation=ReputationState(
                arts=row.reputation_arts,
                engineering=row.reputation_engineering,
                medical=row.reputation_medical,
                humanities=row.reputation_humanities,
            ),
            students=StudentState(
                enrolled=row.enrolled_students,
                averageLevel=row.average_student_level,
            ),
            admissionPolicy=row.admission_policy,
            admissionCriteria=AdmissionCriteria(**(row.admission_criteria or {})),
            buildings=BuildingState(
                classroom=buildings.get("classroom", 0),
                dormitory=buildings.get("dormitory", 0),
                laboratory=buildings.get("laboratory", 0),
                cafeteria=buildings.get("cafeteria", 0),
            ),
            departments=row.departments or [],
            logs=row.logs or [],
        )
```

- [ ] **Step 7: Set up Alembic**

Run: `cd chatbot-server && alembic init alembic`

Edit `alembic.ini`: set `sqlalchemy.url = postgresql+asyncpg://localhost/university_tycoon`

Edit `alembic/env.py` to import `Base` from `app.models.db_models` and set `target_metadata = Base.metadata`.

Create initial migration:
```bash
cd chatbot-server && alembic revision --autogenerate -m "initial tables"
```

- [ ] **Step 8: Commit**

```bash
git add chatbot-server/app/config.py chatbot-server/app/models/db_models.py \
  chatbot-server/app/repositories/base.py chatbot-server/app/repositories/in_memory.py \
  chatbot-server/app/repositories/postgres.py chatbot-server/pyproject.toml \
  chatbot-server/alembic.ini chatbot-server/alembic/
git commit -m "feat: add repository interface, SQLAlchemy models, and Alembic setup"
```

---

### Task 2: Unify Game Logic (Graduation + Admission)

**Files:**
- Modify: `chatbot-server/app/services/game_engine.py`
- Modify: `chatbot-server/app/models/schemas.py`

Reference: `mobile-app/src/utils/gameLogic.ts` (source of truth for unified logic)

- [ ] **Step 1: Add admission_criteria to SaveState schema**

In `chatbot-server/app/models/schemas.py`, add:

```python
class AdmissionCriteria(BaseModel):
    math: int = 5
    science: int = 5
    english: int = 5
    korean: int = 5

class SaveState(BaseModel):
    user_id: str = Field(alias="userId")
    year: int
    month: int
    budget: int
    reputation: ReputationState
    students: StudentState
    admission_policy: AdmissionPolicy = Field(alias="admissionPolicy")
    admission_criteria: AdmissionCriteria = Field(
        default_factory=AdmissionCriteria, alias="admissionCriteria"
    )
    buildings: BuildingState
    departments: list[DepartmentId]
    logs: list[str] = Field(default_factory=list)
```

Keep `admission_policy` for the chatbot UX (easy/normal/hard maps to criteria presets).

- [ ] **Step 2: Unify graduation logic in game_engine.py**

Replace `_apply_graduation` to match mobile app's `applyGraduation`:

```python
def _apply_graduation(self, save: SaveState) -> list[str]:
    graduate_count = max(18, int(save.students.enrolled * 0.24))
    education_power = self._education_power(save)
    research_power = self._research_power(save)
    score = save.students.average_level + education_power * 0.2 + research_power * 0.12

    professor = int(graduate_count * self._clamp(score / 180, 0.04, 0.12))
    startup = int(graduate_count * self._clamp(score / 120, 0.06, 0.16))
    enterprise = int(graduate_count * self._clamp(score / 80, 0.18, 0.32))
    general = max(0, graduate_count - professor - startup - enterprise)
    gained_reputation = professor * 5 + startup * 10 + enterprise * 3 + general

    field = self._leading_reputation_field(save)
    current = getattr(save.reputation, field)
    setattr(save.reputation, field, current + gained_reputation)
    save.students.enrolled = max(20, save.students.enrolled - graduate_count)

    return [
        f"졸업생 {graduate_count}명 배출: 교수 {professor}, 창업 {startup}, 대기업 {enterprise}, 일반 {general}",
        f"{self._field_label(field)} 명성이 {gained_reputation} 상승했습니다.",
    ]
```

- [ ] **Step 3: Fix `_education_power` to use per-department boosts (match mobile app)**

The mobile app uses per-department `educationBoost` values (art=4, computer=5, medical=6, humanities=4).
Update `DepartmentDefinition` and `_education_power`:

```python
# Update DEPARTMENTS to include education_boost per department
DEPARTMENTS: dict[DepartmentId, DepartmentDefinition] = {
    "art": DepartmentDefinition("미술학과", 120, "arts", 35, 4, 4, "예체능 명성 +4 / 학생 수용 +35"),
    "computer": DepartmentDefinition("컴퓨터공학과", 150, "engineering", 45, 4, 5, "공학 명성 +4 / 학생 수용 +45"),
    "medical": DepartmentDefinition("의학과", 180, "medical", 30, 4, 6, "의학 명성 +4 / 학생 수용 +30"),
    "humanities": DepartmentDefinition("인문학과", 100, "humanities", 40, 4, 4, "기초학문 명성 +4 / 학생 수용 +40"),
}
```

Add `education_boost` field to `DepartmentDefinition`:

```python
@dataclass(frozen=True)
class DepartmentDefinition:
    label: str
    cost: int
    field: str
    capacity: int
    reputation_bonus: int
    education_boost: int
    description: str
```

Fix `_education_power`:

```python
def _education_power(self, save: SaveState) -> int:
    dept_boost = sum(DEPARTMENTS[d].education_boost for d in save.departments)
    return save.buildings.classroom * 8 + save.buildings.cafeteria * 2 + dept_boost
```

- [ ] **Step 4: Add helper methods**

```python
def _clamp(self, value: float, min_val: float, max_val: float) -> float:
    return min(max_val, max(min_val, value))

def _leading_reputation_field(self, save: SaveState) -> str:
    # Ordered list ensures deterministic tie-breaking (matches mobile app's Object.entries order)
    fields = [
        ("arts", save.reputation.arts),
        ("engineering", save.reputation.engineering),
        ("medical", save.reputation.medical),
        ("humanities", save.reputation.humanities),
    ]
    return max(fields, key=lambda x: x[1])[0]

def _field_label(self, field: str) -> str:
    return {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}[field]
```

- [ ] **Step 5: Unify admission logic**

Replace `_apply_admission` to use criteria-based calculation matching mobile app:

```python
def _apply_admission(self, save: SaveState) -> list[str]:
    criteria = save.admission_criteria
    criteria_avg = (criteria.math + criteria.science + criteria.english + criteria.korean) / 4
    difficulty_penalty = round(criteria_avg * 7)
    dorm_capacity = save.buildings.dormitory * 40
    freshmen = max(20, 110 - difficulty_penalty + round(dorm_capacity * 0.35))
    capacity = self._capacity(save)
    next_enrolled = min(capacity, freshmen + int(save.students.enrolled * 0.75))
    next_level = max(1.0, 10 - criteria_avg)

    save.students.enrolled = next_enrolled
    save.students.average_level = round(next_level, 1)
    return [
        f"신입생 {freshmen}명이 지원했고, 현재 재학생은 {next_enrolled}명입니다.",
        f"학생 평균 수준 {save.students.average_level}",
    ]
```

- [ ] **Step 6: Update admission policy to set criteria presets**

In the `admission` method, map policy to criteria:

```python
def admission(self, request: KakaoWebhookRequest) -> GameResult:
    save = self._get_or_create(request.user.kakao_user_key)
    policy = self._extract_policy(request)
    if policy is None:
        return self._error("잘못된 입학 정책 요청입니다.", "INVALID_POLICY")

    save.admission_policy = policy
    # Higher criteria = stricter = fewer students but higher level
    presets = {
        "easy": AdmissionCriteria(math=2, science=2, english=2, korean=2),
        "normal": AdmissionCriteria(math=5, science=5, english=5, korean=5),
        "hard": AdmissionCriteria(math=7, science=7, english=7, korean=7),
    }
    save.admission_criteria = presets[policy]
    log = f"입학 정책 변경: {self._policy_label(policy)}"
    save.logs = [log, *save.logs][:5]
    save_repository.put(request.user.kakao_user_key, save)

    return GameResult(
        message=(
            f"입학 정책을 {self._policy_label(policy)}으로 변경했습니다. "
            "다음 입학 시즌부터 반영됩니다."
        ),
        quickReplies=["내 대학 현황", "다음 달 진행", "메인 메뉴"],
        logs=[log],
        save=save,
    )
```

- [ ] **Step 7: Update initial save to include admission_criteria**

```python
def _initial_save(self, user_key: str) -> SaveState:
    return SaveState(
        userId=user_key,
        year=1, month=1, budget=480,
        reputation=ReputationState(arts=6, engineering=6, medical=6, humanities=12),
        students=StudentState(enrolled=72, averageLevel=5.0),
        admissionPolicy="normal",
        admissionCriteria=AdmissionCriteria(math=5, science=5, english=5, korean=5),
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0),
        departments=["humanities"],
        logs=["작은 캠퍼스로 새 학기를 시작했습니다."],
    )
```

- [ ] **Step 8: Commit**

```bash
git add chatbot-server/app/models/schemas.py chatbot-server/app/services/game_engine.py
git commit -m "feat: unify graduation and admission logic with mobile app"
```

---

### Task 3: pytest Setup + GameEngine Unit Tests

**Files:**
- Create: `chatbot-server/tests/__init__.py`
- Create: `chatbot-server/tests/conftest.py`
- Create: `chatbot-server/tests/test_game_engine.py`
- Create: `chatbot-server/tests/test_graduation.py`
- Create: `chatbot-server/tests/test_admission.py`

**Note:** Task 3 tests use synchronous calls. Task 4 will convert GameEngine to async; at that point all tests must be updated to `async def` with `await`. Task 4 includes a step for this migration.

- [ ] **Step 1: Create `tests/__init__.py`**

Create an empty `chatbot-server/tests/__init__.py` file.

- [ ] **Step 2: Create conftest.py with fixtures**

```python
# chatbot-server/tests/conftest.py
import pytest
from app.models.schemas import (
    ActionPayload, AdmissionCriteria, BuildingState, KakaoUser,
    KakaoWebhookRequest, ReputationState, SaveState, StudentState,
)
from app.repositories.in_memory import InMemorySaveRepository
from app.services.game_engine import GameEngine

@pytest.fixture
def repo() -> InMemorySaveRepository:
    return InMemorySaveRepository()

@pytest.fixture
def engine(repo: InMemorySaveRepository, monkeypatch: pytest.MonkeyPatch) -> GameEngine:
    import app.services.game_engine as mod
    monkeypatch.setattr(mod, "save_repository", repo)
    return GameEngine()

@pytest.fixture
def user_key() -> str:
    return "test_user_001"

@pytest.fixture
def webhook(user_key: str) -> KakaoWebhookRequest:
    return KakaoWebhookRequest(user=KakaoUser(kakaoUserKey=user_key))

def make_webhook(user_key: str = "test_user_001", action_name: str = "ACTION_STATUS", **params) -> KakaoWebhookRequest:
    return KakaoWebhookRequest(
        user=KakaoUser(kakaoUserKey=user_key),
        action=ActionPayload(name=action_name, params=params),
    )

def make_save(user_key: str = "test_user_001", **overrides) -> SaveState:
    defaults = dict(
        userId=user_key, year=1, month=1, budget=480,
        reputation=ReputationState(arts=6, engineering=6, medical=6, humanities=12),
        students=StudentState(enrolled=72, averageLevel=5.0),
        admissionPolicy="normal",
        admissionCriteria=AdmissionCriteria(math=5, science=5, english=5, korean=5),
        buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0),
        departments=["humanities"],
        logs=[],
    )
    defaults.update(overrides)
    return SaveState(**defaults)
```

- [ ] **Step 3: Write core GameEngine tests**

```python
# chatbot-server/tests/test_game_engine.py
from tests.conftest import make_webhook, make_save

def test_start_game_creates_save(engine, repo, webhook):
    result = engine.start_game(webhook)
    assert result.ok is True
    assert result.save is not None
    assert result.save.budget == 480
    assert result.save.year == 1

def test_load_status_returns_state(engine, repo, user_key, webhook):
    engine.start_game(webhook)
    result = engine.load_status(webhook)
    assert "예산 480G" in result.message

def test_advance_turn_increments_month(engine, webhook):
    engine.start_game(webhook)
    result = engine.advance_turn(webhook)
    assert result.save.month == 2

def test_advance_turn_wraps_year(engine, repo, user_key):
    save = make_save(user_key=user_key, month=12, year=1)
    repo.put(user_key, save)
    result = engine.advance_turn(make_webhook(user_key))
    assert result.save.month == 1
    assert result.save.year == 2

def test_build_classroom_deducts_budget(engine, webhook):
    engine.start_game(webhook)
    req = make_webhook(action_name="ACTION_BUILD_CLASSROOM")
    result = engine.build(req)
    assert result.ok is True
    assert result.save.budget == 480 - 120
    assert result.save.buildings.classroom == 2

def test_build_insufficient_budget(engine, repo, user_key):
    save = make_save(user_key=user_key, budget=50)
    repo.put(user_key, save)
    result = engine.build(make_webhook(action_name="ACTION_BUILD_CLASSROOM"))
    assert result.ok is False
    assert result.error_code == "NOT_ENOUGH_BUDGET"

def test_department_open(engine, webhook):
    engine.start_game(webhook)
    req = make_webhook(action_name="ACTION_DEPT_COMPUTER")
    result = engine.department(req)
    assert result.ok is True
    assert "computer" in result.save.departments

def test_department_duplicate(engine, webhook):
    engine.start_game(webhook)
    req = make_webhook(action_name="ACTION_DEPT_HUMANITIES")
    result = engine.department(req)
    assert result.ok is False
    assert result.error_code == "ALREADY_OPENED"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd chatbot-server && python -m pytest tests/test_game_engine.py -v`
Expected: All PASS

- [ ] **Step 5: Write graduation-specific tests**

```python
# chatbot-server/tests/test_graduation.py
from tests.conftest import make_webhook, make_save

def test_graduation_fires_in_february(engine, repo, user_key):
    save = make_save(user_key=user_key, month=1)
    repo.put(user_key, save)
    result = engine.advance_turn(make_webhook(user_key))
    assert result.save.month == 2
    grad_logs = [l for l in result.logs if "졸업생" in l]
    assert len(grad_logs) == 1

def test_graduation_distributes_to_leading_field(engine, repo, user_key):
    save = make_save(
        user_key=user_key, month=1,
        reputation={"arts": 100, "engineering": 6, "medical": 6, "humanities": 12},
    )
    repo.put(user_key, save)
    result = engine.advance_turn(make_webhook(user_key))
    assert result.save.reputation.arts > 100

def test_graduation_reduces_students(engine, repo, user_key):
    save = make_save(user_key=user_key, month=1)
    repo.put(user_key, save)
    before = save.students.enrolled
    result = engine.advance_turn(make_webhook(user_key))
    assert result.save.students.enrolled < before
```

- [ ] **Step 6: Write admission-specific tests**

```python
# chatbot-server/tests/test_admission.py
from app.models.schemas import AdmissionCriteria
from tests.conftest import make_webhook, make_save

def test_admission_fires_in_march(engine, repo, user_key):
    save = make_save(user_key=user_key, month=2)
    repo.put(user_key, save)
    result = engine.advance_turn(make_webhook(user_key))
    assert result.save.month == 3
    adm_logs = [l for l in result.logs if "신입생" in l]
    assert len(adm_logs) == 1

def test_strict_criteria_yields_fewer_students(engine, repo, user_key):
    # Low criteria values = lenient = more students
    save_lenient = make_save(
        user_key=user_key, month=2,
        admissionCriteria=AdmissionCriteria(math=2, science=2, english=2, korean=2),
    )
    repo.put(user_key, save_lenient)
    result_lenient = engine.advance_turn(make_webhook(user_key))
    enrolled_lenient = result_lenient.save.students.enrolled

    # High criteria values = strict = fewer students
    save_strict = make_save(
        user_key=user_key, month=2,
        admissionCriteria=AdmissionCriteria(math=7, science=7, english=7, korean=7),
    )
    repo.put(user_key, save_strict)
    result_strict = engine.advance_turn(make_webhook(user_key))
    enrolled_strict = result_strict.save.students.enrolled

    assert enrolled_lenient > enrolled_strict

def test_policy_sets_criteria_presets(engine, webhook):
    engine.start_game(webhook)
    req = make_webhook(action_name="ACTION_ADMISSION_HARD")
    result = engine.admission(req)
    # "hard" policy = high criteria = strict admission
    assert result.save.admission_criteria.math == 7
```

- [ ] **Step 7: Run all tests**

Run: `cd chatbot-server && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add chatbot-server/tests/
git commit -m "test: add GameEngine unit tests for core loop, graduation, admission"
```

---

### Task 4: Wire Async DB into FastAPI

**Depends on:** Task 1

**Files:**
- Modify: `chatbot-server/app/main.py`
- Modify: `chatbot-server/app/api/routes/kakao.py`
- Modify: `chatbot-server/app/api/routes/health.py`
- Modify: `chatbot-server/app/services/game_engine.py` (make methods accept repo param)

- [ ] **Step 1: Add DB session engine to main.py**

```python
# chatbot-server/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.config import settings

engine_db = None
async_session_factory = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine_db, async_session_factory
    if settings.use_db:
        engine_db = create_async_engine(settings.async_database_url)
        async_session_factory = async_sessionmaker(engine_db, expire_on_commit=False)
    yield
    if engine_db:
        await engine_db.dispose()

app = FastAPI(
    title="University Tycoon Chatbot Server",
    version="0.1.0",
    description="Kakao chatbot skill server for University Tycoon.",
    lifespan=lifespan,
)

from app.api.routes.health import router as health_router
from app.api.routes.kakao import router as kakao_router

app.include_router(health_router)
app.include_router(kakao_router, prefix="/webhooks/kakao", tags=["kakao"])
```

- [ ] **Step 2: Create dependency injection for repository**

Add to `chatbot-server/app/api/deps.py`:

```python
# chatbot-server/app/api/deps.py
from collections.abc import AsyncGenerator
from fastapi import Depends
from app.config import settings
from app.repositories.base import SaveRepository
from app.repositories.in_memory import save_repository as in_memory_repo

async def get_repository() -> AsyncGenerator[SaveRepository]:
    if not settings.use_db:
        yield in_memory_repo
        return
    from app.main import async_session_factory
    from app.repositories.postgres import PostgresSaveRepository
    async with async_session_factory() as session:
        yield PostgresSaveRepository(session)
```

- [ ] **Step 3: Refactor GameEngine to accept repository**

Change `GameEngine` methods to accept a `repo: SaveRepository` parameter instead of using global `save_repository`. Update `_get_or_create` and all methods that call `save_repository.put()`:

```python
async def start_game(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
    save = self._initial_save(request.user.kakao_user_key)
    await repo.put(request.user.kakao_user_key, save)
    ...

async def _get_or_create(self, user_key: str, repo: SaveRepository) -> SaveState:
    save = await repo.get(user_key)
    if save is None:
        save = self._initial_save(user_key)
        await repo.put(user_key, save)
    return save
```

All public methods become `async` and take `repo` parameter.

- [ ] **Step 4: Update kakao routes to use Depends**

```python
# chatbot-server/app/api/routes/kakao.py
from fastapi import APIRouter, Depends
from app.models.schemas import KakaoWebhookRequest
from app.services.game_engine import game_engine
from app.services.kakao_adapter import to_kakao_response
from app.api.deps import get_repository
from app.repositories.base import SaveRepository

router = APIRouter()

@router.post("/start-game")
async def start_game(request: KakaoWebhookRequest, repo: SaveRepository = Depends(get_repository)) -> dict:
    result = await game_engine.start_game(request, repo)
    return to_kakao_response(result)

# ... same pattern for all other endpoints
```

- [ ] **Step 5: Update health check to verify DB**

```python
# chatbot-server/app/api/routes/health.py
from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health():
    status = {"status": "ok", "db": "disabled"}
    if settings.use_db:
        try:
            from app.main import engine_db
            from sqlalchemy import text
            async with engine_db.connect() as conn:
                await conn.execute(text("SELECT 1"))
            status["db"] = "connected"
        except Exception as e:
            status["db"] = f"error: {e}"
    return status
```

- [ ] **Step 6: Run tests and fix any breakage**

Run: `cd chatbot-server && python -m pytest tests/ -v`
Update test fixtures for async methods if needed.

- [ ] **Step 7: Commit**

```bash
git add chatbot-server/app/
git commit -m "feat: wire async DB session and repository dependency injection"
```

---

### Task 5: Integration Tests for API Endpoints

**Depends on:** Task 2, Task 3

**Files:**
- Create: `chatbot-server/tests/test_api.py`

- [ ] **Step 1: Write API integration tests using TestClient**

```python
# chatbot-server/tests/test_api.py
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)

PAYLOAD = {"user": {"kakaoUserKey": "integration_test_user"}}

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_start_game_returns_kakao_format(client):
    resp = client.post("/webhooks/kakao/start-game", json=PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "2.0"
    assert "template" in body
    assert "outputs" in body["template"]
    assert "quickReplies" in body["template"]

def test_full_game_loop(client):
    client.post("/webhooks/kakao/start-game", json=PAYLOAD)

    resp = client.post("/webhooks/kakao/status", json=PAYLOAD)
    assert "예산 480G" in resp.json()["template"]["outputs"][0]["simpleText"]["text"]

    resp = client.post("/webhooks/kakao/advance-turn", json=PAYLOAD)
    assert resp.status_code == 200

    build_payload = {**PAYLOAD, "action": {"name": "ACTION_BUILD_CLASSROOM", "params": {}}}
    resp = client.post("/webhooks/kakao/build", json=build_payload)
    assert resp.status_code == 200

    dept_payload = {**PAYLOAD, "action": {"name": "ACTION_DEPT_COMPUTER", "params": {}}}
    resp = client.post("/webhooks/kakao/department", json=dept_payload)
    assert resp.status_code == 200

    admission_payload = {**PAYLOAD, "action": {"name": "ACTION_ADMISSION_HARD", "params": {}}}
    resp = client.post("/webhooks/kakao/admission", json=admission_payload)
    assert resp.status_code == 200

def test_kakao_response_has_quick_replies(client):
    client.post("/webhooks/kakao/start-game", json=PAYLOAD)
    resp = client.post("/webhooks/kakao/status", json=PAYLOAD)
    qrs = resp.json()["template"]["quickReplies"]
    assert len(qrs) > 0
    assert all("label" in qr for qr in qrs)
```

- [ ] **Step 2: Run integration tests**

Run: `cd chatbot-server && python -m pytest tests/test_api.py -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add chatbot-server/tests/test_api.py
git commit -m "test: add API integration tests for Kakao webhook endpoints"
```

---

### Task 6: Deploy to Render

**Depends on:** Task 4

**Files:**
- Create: `chatbot-server/Dockerfile`
- Create: `chatbot-server/render.yaml`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
# chatbot-server/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY app/ app/
COPY alembic.ini .
COPY alembic/ alembic/

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

- [ ] **Step 2: Create render.yaml blueprint**

```yaml
# chatbot-server/render.yaml
databases:
  - name: university-tycoon-db
    plan: free
    databaseName: university_tycoon
    region: singapore

services:
  - type: web
    name: university-tycoon-chatbot
    runtime: docker
    dockerfilePath: ./chatbot-server/Dockerfile
    dockerContext: ./chatbot-server
    region: singapore
    plan: free
    envVars:
      - key: UT_USE_DB
        value: "true"
      - key: UT_DATABASE_URL
        fromDatabase:
          name: university-tycoon-db
          property: connectionString
        # config.py auto-converts postgresql:// to postgresql+asyncpg://
    healthCheckPath: /health
```

- [ ] **Step 3: Test Docker build locally**

```bash
cd chatbot-server && docker build -t ut-chatbot .
```

- [ ] **Step 4: Deploy to Render**

1. Push code to GitHub repository
2. Go to https://dashboard.render.com
3. New > Blueprint > connect repo > select `render.yaml`
4. Render creates the DB and web service
5. `UT_DATABASE_URL` is auto-set from the Render DB; `config.py` auto-converts `postgresql://` to `postgresql+asyncpg://`

- [ ] **Step 5: Verify deployment**

```bash
curl https://<your-render-url>/health
```

Expected: `{"status": "ok", "db": "connected"}`

- [ ] **Step 6: Test live endpoints**

```bash
curl -X POST https://<your-render-url>/webhooks/kakao/start-game \
  -H "Content-Type: application/json" \
  -d '{"user": {"kakaoUserKey": "manual_test"}}'
```

Expected: Kakao-format JSON response with "작은 대학 운영이 시작되었습니다."

- [ ] **Step 7: Commit**

```bash
git add chatbot-server/Dockerfile chatbot-server/render.yaml
git commit -m "feat: add Dockerfile and Render deployment blueprint"
```

---

### Task 7: Kakao Open Builder Wiring Guide

**Depends on:** Task 6

**Files:**
- Create: `docs/kakao-openbuilder-setup.md`

This task is a documentation/configuration task, not code. It documents the manual steps to connect the deployed server to Kakao Open Builder.

- [ ] **Step 1: Document Open Builder setup steps**

Create `docs/kakao-openbuilder-setup.md` with:

```markdown
# Kakao Open Builder 연동 가이드

## 사전 준비
1. Kakao Developers 계정 생성: https://developers.kakao.com
2. 카카오톡 채널 생성 (카카오 비즈니스 > 카카오톡 채널)
3. 오픈빌더에서 봇 생성: https://chatbot.kakao.com

## 스킬 서버 등록
1. 오픈빌더 > 스킬 > 스킬 생성
2. URL: `https://<your-render-url>/webhooks/kakao`
3. 각 스킬별 엔드포인트 등록:

| 스킬 이름 | URL 경로 |
|-----------|----------|
| 게임 시작 | /webhooks/kakao/start-game |
| 대학 현황 | /webhooks/kakao/status |
| 다음 달 진행 | /webhooks/kakao/advance-turn |
| 건설 메뉴 | /webhooks/kakao/build-menu |
| 건물 건설 | /webhooks/kakao/build |
| 학과 메뉴 | /webhooks/kakao/department-menu |
| 학과 개설 | /webhooks/kakao/department |
| 입학 정책 메뉴 | /webhooks/kakao/admission-menu |
| 입학 정책 변경 | /webhooks/kakao/admission |
| 운영 기록 | /webhooks/kakao/logs |

## 시나리오 블록 설정

### 웰컴 블록
- 트리거: 사용자 최초 진입
- 스킬: 게임 시작
- 빠른 답장: 내 대학 현황, 건물 건설, 학과 개설, 다음 달 진행

### 메인 메뉴 블록
- 트리거: "내 대학 현황", "메인 메뉴"
- 스킬: 대학 현황

### 턴 진행 블록
- 트리거: "다음 달 진행"
- 스킬: 다음 달 진행

### 건설 블록
- 트리거: "건물 건설", "계속 건설"
- 스킬: 건설 메뉴

### 건물 선택 블록 (4개)
- 트리거: "강의실 건설", "기숙사 건설", "연구소 건설", "식당 건설"
- 스킬: 건물 건설
- 파라미터: buildingType = classroom / dormitory / laboratory / cafeteria

### 학과 블록
- 트리거: "학과 개설", "다른 학과 보기"
- 스킬: 학과 메뉴

### 학과 선택 블록 (4개)
- 트리거: "미술학과", "컴퓨터공학과", "의학과", "인문학과"
- 스킬: 학과 개설
- 파라미터: departmentId = art / computer / medical / humanities

### 입학 정책 블록
- 트리거: "입학 정책"
- 스킬: 입학 정책 메뉴

### 정책 선택 블록 (3개)
- 트리거: "쉬움", "보통", "엄격"
- 스킬: 입학 정책 변경
- 파라미터: policyLevel = easy / normal / hard

### 기록 블록
- 트리거: "지난 결과 보기"
- 스킬: 운영 기록

## 테스트
1. 오픈빌더 > 봇 테스트에서 시나리오 동작 확인
2. 카카오톡 채널에 봇 배포
3. 카카오톡에서 채널 친구 추가 후 대화 시작
```

- [ ] **Step 2: Commit**

```bash
git add docs/kakao-openbuilder-setup.md
git commit -m "docs: add Kakao Open Builder wiring guide"
```
