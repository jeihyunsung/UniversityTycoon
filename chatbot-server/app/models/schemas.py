from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AdmissionPolicy = Literal["easy", "normal", "hard"]
BuildingType = Literal["classroom", "dormitory", "laboratory", "cafeteria"]
DepartmentId = Literal["art", "computer", "medical", "humanities"]


class KakaoUser(BaseModel):
    id: str
    type: str = "botUserKey"
    properties: dict[str, Any] = Field(default_factory=dict)


class UserRequest(BaseModel):
    timezone: str = "Asia/Seoul"
    utterance: str = ""
    user: KakaoUser
    block: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    lang: str | None = None
    callback_url: str | None = Field(default=None, alias="callbackUrl")


class ActionPayload(BaseModel):
    name: str = "ACTION_STATUS"
    params: dict[str, Any] = Field(default_factory=dict)
    id: str | None = None
    client_extra: Any = Field(default=None, alias="clientExtra")
    detail_params: dict[str, Any] = Field(default_factory=dict, alias="detailParams")


class KakaoWebhookRequest(BaseModel):
    """Matches the actual Kakao Open Builder webhook payload format."""
    user_request: UserRequest = Field(alias="userRequest")
    action: ActionPayload = Field(default_factory=ActionPayload)
    bot: dict[str, Any] = Field(default_factory=dict)
    intent: dict[str, Any] = Field(default_factory=dict)

    @property
    def user(self) -> KakaoUser:
        return self.user_request.user


class StudentState(BaseModel):
    enrolled: int
    average_level: float = Field(alias="averageLevel")


class ReputationState(BaseModel):
    arts: int
    engineering: int
    medical: int
    humanities: int


class BuildingState(BaseModel):
    classroom: int
    dormitory: int
    laboratory: int
    cafeteria: int


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
    buildings: BuildingState
    departments: list[DepartmentId]
    logs: list[str] = Field(default_factory=list)
    admission_criteria: AdmissionCriteria = Field(
        default_factory=AdmissionCriteria, alias="admissionCriteria"
    )
    pending_event: str | None = Field(default=None, alias="pendingEvent")
    bonus_freshmen: int = Field(default=0, alias="bonusFreshmen")
    completed_milestones: list[str] = Field(default_factory=list, alias="completedMilestones")
    active_quest_lines: list[str] = Field(default_factory=list, alias="activeQuestLines")
    completed_quests: list[str] = Field(default_factory=list, alias="completedQuests")
    title: str = Field(default="신생 대학", alias="title")
    admission_changed: bool = Field(default=False, alias="admissionChanged")


class GameResult(BaseModel):
    ok: bool = True
    message: str
    quick_replies: list[str] = Field(default_factory=list, alias="quickReplies")
    logs: list[str] = Field(default_factory=list)
    options: list[dict[str, Any]] = Field(default_factory=list)
    error_code: str | None = Field(default=None, alias="errorCode")
    save: SaveState | None = None
    image_url: str | None = Field(default=None, alias="imageUrl")
    image_title: str | None = Field(default=None, alias="imageTitle")
    image_prompt: str | None = Field(default=None, alias="imagePrompt")
    image_negative_prompt: str | None = Field(default=None, alias="imageNegativePrompt")
