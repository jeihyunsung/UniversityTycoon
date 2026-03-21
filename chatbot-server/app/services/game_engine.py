from __future__ import annotations

from dataclasses import dataclass

from app.models.schemas import (
    AdmissionCriteria,
    AdmissionPolicy,
    BuildingState,
    BuildingType,
    DepartmentId,
    GameResult,
    KakaoWebhookRequest,
    ReputationState,
    SaveState,
    StudentState,
)
from app.repositories.base import SaveRepository
from app.services.image_service import ImageGenerator, NullImageGenerator, PromptBuilder


MONTH_LABELS = {
    1: "1월",
    2: "2월",
    3: "3월",
    4: "4월",
    5: "5월",
    6: "6월",
    7: "7월",
    8: "8월",
    9: "9월",
    10: "10월",
    11: "11월",
    12: "12월",
}


@dataclass(frozen=True)
class BuildingDefinition:
    label: str
    cost: int
    capacity: int
    education: int
    research: int
    dorm: int
    description: str


@dataclass(frozen=True)
class DepartmentDefinition:
    label: str
    cost: int
    field: str
    capacity: int
    reputation_bonus: int
    education_boost: int
    description: str


BUILDINGS: dict[BuildingType, BuildingDefinition] = {
    "classroom": BuildingDefinition("강의실", 120, 60, 8, 0, 0, "학생 수용량 +60 / 교육력 +8"),
    "dormitory": BuildingDefinition("기숙사", 140, 0, 0, 0, 40, "기숙사 수용 +40"),
    "laboratory": BuildingDefinition("연구소", 180, 0, 0, 10, 0, "연구력 +10"),
    "cafeteria": BuildingDefinition("식당", 90, 0, 2, 0, 0, "학생 만족 보정 / 교육력 +2"),
}

DEPARTMENTS: dict[DepartmentId, DepartmentDefinition] = {
    "art": DepartmentDefinition("미술학과", 120, "arts", 35, 4, 4, "예체능 명성 +4 / 학생 수용 +35"),
    "computer": DepartmentDefinition("컴퓨터공학과", 150, "engineering", 45, 4, 5, "공학 명성 +4 / 학생 수용 +45"),
    "medical": DepartmentDefinition("의학과", 180, "medical", 30, 4, 6, "의학 명성 +4 / 학생 수용 +30"),
    "humanities": DepartmentDefinition("인문학과", 100, "humanities", 40, 4, 4, "기초학문 명성 +4 / 학생 수용 +40"),
}


class GameEngine:
    def __init__(self, image_generator: ImageGenerator | None = None) -> None:
        self._image_gen = image_generator or NullImageGenerator()

    async def start_game(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = self._initial_save(request.user.kakao_user_key)
        await repo.put(request.user.kakao_user_key, save)
        prompt, neg = PromptBuilder.build("start_game", "", save.month)
        image_url = await self._image_gen.generate(prompt, neg)
        return GameResult(
            message="작은 대학 운영이 시작되었습니다. 현재 1년 1월 / 예산 480G / 총 명성 30",
            quickReplies=["내 대학 현황", "건물 건설", "학과 개설", "다음 달 진행"],
            save=save,
            imageUrl=image_url,
            imageTitle="🎓 대학교 설립!",
        )

    async def load_status(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        total_reputation = self._total_reputation(save)
        return GameResult(
            message=(
                f"{save.year}년 {MONTH_LABELS[save.month]}입니다. "
                f"예산 {save.budget}G / 총 명성 {total_reputation} / 재학생 {save.students.enrolled}명"
            ),
            quickReplies=["다음 달 진행", "건물 건설", "학과 개설", "입학 정책", "지난 결과 보기"],
            logs=save.logs[:1],
            save=save,
        )

    async def advance_turn(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        next_month = 1 if save.month == 12 else save.month + 1
        next_year = save.year + 1 if save.month == 12 else save.year
        monthly_delta = self._monthly_budget_delta(save)
        save.budget = max(0, save.budget + monthly_delta)
        logs = [f"운영 결과 {monthly_delta:+}G"]

        save.month = next_month
        save.year = next_year

        if save.month == 2:
            logs.extend(self._apply_graduation(save))
        if save.month == 3:
            logs.extend(self._apply_admission(save))
        if save.month == 10:
            logs.append("10월입니다. 입학 정책을 점검할 시기입니다.")

        save.logs = [f"{save.year}년 {MONTH_LABELS[save.month]} 진입", *logs, *save.logs][:5]
        await repo.put(request.user.kakao_user_key, save)

        return GameResult(
            message=(
                f"{save.year}년 {MONTH_LABELS[save.month]}입니다. "
                f"이번 달 운영 변화는 {monthly_delta:+}G입니다."
            ),
            logs=logs,
            quickReplies=["다음 달 진행", "건물 건설", "학과 개설", "내 대학 현황"],
            save=save,
        )

    async def build_menu(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        options = [
            {
                "label": f"{definition.label} {definition.cost}G",
                "description": f"{definition.description} / 보유 {getattr(save.buildings, key)}개",
            }
            for key, definition in BUILDINGS.items()
        ]
        return GameResult(
            message=f"현재 예산은 {save.budget}G입니다. 건설할 시설을 고르세요.",
            options=options,
            quickReplies=["강의실 건설", "기숙사 건설", "연구소 건설", "식당 건설", "메인 메뉴"],
            save=save,
        )

    async def build(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        building_type = self._extract_building_type(request)
        if building_type is None:
            return self._error("잘못된 건물 요청입니다.", "INVALID_ACTION")

        definition = BUILDINGS[building_type]
        if save.budget < definition.cost:
            return self._error(
                f"예산이 부족합니다. 현재 예산은 {save.budget}G입니다.",
                "NOT_ENOUGH_BUDGET",
                ["내 대학 현황", "다음 달 진행"],
            )

        setattr(save.buildings, building_type, getattr(save.buildings, building_type) + 1)
        save.budget -= definition.cost
        log = f"{definition.label} 건설 완료"
        save.logs = [log, *save.logs][:5]
        await repo.put(request.user.kakao_user_key, save)

        prompt, neg = PromptBuilder.build("building", building_type, save.month)
        image_url = await self._image_gen.generate(prompt, neg)
        return GameResult(
            message=f"{definition.label}을 건설했습니다. 예산 -{definition.cost}G / {definition.description}",
            quickReplies=["계속 건설", "내 대학 현황", "다음 달 진행"],
            logs=[log],
            save=save,
            imageUrl=image_url,
            imageTitle=f"🏗️ {definition.label} 건설!",
        )

    async def department_menu(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        options = []
        for department_id, definition in DEPARTMENTS.items():
            opened = department_id in save.departments
            status = "이미 개설됨" if opened else definition.description
            options.append({"label": f"{definition.label} {definition.cost}G", "description": status})

        return GameResult(
            message="개설할 학과를 고르세요.",
            options=options,
            quickReplies=["미술학과", "컴퓨터공학과", "의학과", "인문학과", "메인 메뉴"],
            save=save,
        )

    async def department(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        department_id = self._extract_department_id(request)
        if department_id is None:
            return self._error("잘못된 학과 요청입니다.", "INVALID_ACTION")
        if department_id in save.departments:
            return self._error("이미 개설된 학과입니다.", "ALREADY_OPENED", ["내 대학 현황", "메인 메뉴"])

        definition = DEPARTMENTS[department_id]
        if save.budget < definition.cost:
            return self._error(
                f"예산이 부족합니다. 현재 예산은 {save.budget}G입니다.",
                "NOT_ENOUGH_BUDGET",
                ["내 대학 현황", "다음 달 진행"],
            )

        save.budget -= definition.cost
        save.departments.append(department_id)
        current_value = getattr(save.reputation, definition.field)
        setattr(save.reputation, definition.field, current_value + definition.reputation_bonus)
        log = f"{definition.label} 개설 완료"
        save.logs = [log, *save.logs][:5]
        await repo.put(request.user.kakao_user_key, save)

        prompt, neg = PromptBuilder.build("department", department_id, save.month)
        image_url = await self._image_gen.generate(prompt, neg)
        return GameResult(
            message=f"{definition.label}를 개설했습니다. 예산 -{definition.cost}G / {definition.description}",
            quickReplies=["다른 학과 보기", "내 대학 현황", "다음 달 진행"],
            logs=[log],
            save=save,
            imageUrl=image_url,
            imageTitle=f"📚 {definition.label} 개설!",
        )

    async def admission_menu(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        return GameResult(
            message=(
                f"현재 입학 정책은 {self._policy_label(save.admission_policy)}입니다. "
                "정책이 엄격할수록 학생 평균 수준은 오르지만 입학생 수는 줄어듭니다."
            ),
            quickReplies=["쉬움", "보통", "엄격", "메인 메뉴"],
            save=save,
        )

    async def admission(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        policy = self._extract_policy(request)
        if policy is None:
            return self._error("잘못된 입학 정책 요청입니다.", "INVALID_POLICY")

        save.admission_policy = policy
        criteria_presets: dict[AdmissionPolicy, AdmissionCriteria] = {
            "easy": AdmissionCriteria(math=2, science=2, english=2, korean=2),
            "normal": AdmissionCriteria(math=5, science=5, english=5, korean=5),
            "hard": AdmissionCriteria(math=7, science=7, english=7, korean=7),
        }
        save.admission_criteria = criteria_presets[policy]
        log = f"입학 정책 변경: {self._policy_label(policy)}"
        save.logs = [log, *save.logs][:5]
        await repo.put(request.user.kakao_user_key, save)

        return GameResult(
            message=(
                f"입학 정책을 {self._policy_label(policy)}으로 변경했습니다. "
                "다음 입학 시즌부터 반영됩니다."
            ),
            quickReplies=["내 대학 현황", "다음 달 진행", "메인 메뉴"],
            logs=[log],
            save=save,
        )

    async def logs(self, request: KakaoWebhookRequest, repo: SaveRepository) -> GameResult:
        save = await self._get_or_create(request.user.kakao_user_key, repo)
        return GameResult(
            message="최근 운영 기록입니다.",
            logs=save.logs[:5],
            quickReplies=["내 대학 현황", "다음 달 진행", "메인 메뉴"],
            save=save,
        )

    def _initial_save(self, user_key: str) -> SaveState:
        return SaveState(
            userId=user_key,
            year=1,
            month=1,
            budget=480,
            reputation=ReputationState(arts=6, engineering=6, medical=6, humanities=12),
            students=StudentState(enrolled=72, averageLevel=5.0),
            admissionPolicy="normal",
            buildings=BuildingState(classroom=1, dormitory=1, laboratory=0, cafeteria=0),
            departments=["humanities"],
            logs=["작은 캠퍼스로 새 학기를 시작했습니다."],
            admissionCriteria=AdmissionCriteria(math=5, science=5, english=5, korean=5),
        )

    async def _get_or_create(self, user_key: str, repo: SaveRepository) -> SaveState:
        save = await repo.get(user_key)
        if save is None:
            save = self._initial_save(user_key)
            await repo.put(user_key, save)
        return save

    def _extract_building_type(self, request: KakaoWebhookRequest) -> BuildingType | None:
        value = request.action.params.get("buildingType")
        if isinstance(value, str) and value in BUILDINGS:
            return value
        name = request.action.name
        mapping = {
            "ACTION_BUILD_CLASSROOM": "classroom",
            "ACTION_BUILD_DORMITORY": "dormitory",
            "ACTION_BUILD_LAB": "laboratory",
            "ACTION_BUILD_CAFETERIA": "cafeteria",
        }
        return mapping.get(name)  # type: ignore[return-value]

    def _extract_department_id(self, request: KakaoWebhookRequest) -> DepartmentId | None:
        value = request.action.params.get("departmentId")
        if isinstance(value, str) and value in DEPARTMENTS:
            return value
        mapping = {
            "ACTION_DEPT_ART": "art",
            "ACTION_DEPT_COMPUTER": "computer",
            "ACTION_DEPT_MEDICAL": "medical",
            "ACTION_DEPT_HUMANITIES": "humanities",
        }
        return mapping.get(request.action.name)  # type: ignore[return-value]

    def _extract_policy(self, request: KakaoWebhookRequest) -> AdmissionPolicy | None:
        value = request.action.params.get("policyLevel")
        if value in {"easy", "normal", "hard"}:
            return value
        mapping = {
            "ACTION_ADMISSION_EASY": "easy",
            "ACTION_ADMISSION_NORMAL": "normal",
            "ACTION_ADMISSION_HARD": "hard",
        }
        return mapping.get(request.action.name)  # type: ignore[return-value]

    def _total_reputation(self, save: SaveState) -> int:
        return (
            save.reputation.arts
            + save.reputation.engineering
            + save.reputation.medical
            + save.reputation.humanities
        )

    def _monthly_budget_delta(self, save: SaveState) -> int:
        income = int(save.students.enrolled * 3.2)
        building_count = (
            save.buildings.classroom
            + save.buildings.dormitory
            + save.buildings.laboratory
            + save.buildings.cafeteria
        )
        maintenance = building_count * 18 + len(save.departments) * 14
        return income - maintenance

    def _capacity(self, save: SaveState) -> int:
        department_capacity = sum(DEPARTMENTS[department].capacity for department in save.departments)
        building_capacity = save.buildings.classroom * 60
        return department_capacity + building_capacity

    def _research_power(self, save: SaveState) -> int:
        return save.buildings.laboratory * 10 + len(save.departments) * 2

    def _education_power(self, save: SaveState) -> int:
        dept_boost = sum(DEPARTMENTS[d].education_boost for d in save.departments)
        return save.buildings.classroom * 8 + save.buildings.cafeteria * 2 + dept_boost

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

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        return min(max_val, max(min_val, value))

    def _leading_reputation_field(self, save: SaveState) -> str:
        fields = [
            ("arts", save.reputation.arts),
            ("engineering", save.reputation.engineering),
            ("medical", save.reputation.medical),
            ("humanities", save.reputation.humanities),
        ]
        return max(fields, key=lambda x: x[1])[0]

    def _field_label(self, field: str) -> str:
        return {"arts": "예체능", "engineering": "공학", "medical": "의학", "humanities": "기초학문"}[field]

    def _policy_label(self, policy: AdmissionPolicy) -> str:
        return {"easy": "쉬움", "normal": "보통", "hard": "엄격"}[policy]

    def _error(self, message: str, code: str, quick_replies: list[str] | None = None) -> GameResult:
        return GameResult(
            ok=False,
            message=message,
            errorCode=code,
            quickReplies=quick_replies or ["내 대학 현황", "메인 메뉴"],
        )
