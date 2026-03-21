from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AdmissionPolicy = Literal["easy", "normal", "hard"]
BuildingType = Literal["classroom", "dormitory", "laboratory", "cafeteria"]
DepartmentId = Literal["art", "computer", "medical", "humanities"]


class KakaoUser(BaseModel):
    kakao_user_key: str = Field(alias="kakaoUserKey")


class ActionPayload(BaseModel):
    name: str = "ACTION_STATUS"
    params: dict[str, Any] = Field(default_factory=dict)


class ContextPayload(BaseModel):
    channel_id: str | None = Field(default=None, alias="channelId")
    block_id: str | None = Field(default=None, alias="blockId")


class KakaoWebhookRequest(BaseModel):
    user: KakaoUser
    action: ActionPayload = Field(default_factory=ActionPayload)
    context: ContextPayload = Field(default_factory=ContextPayload)
    raw_kakao_payload: dict[str, Any] = Field(default_factory=dict, alias="rawKakaoPayload")


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


class GameResult(BaseModel):
    ok: bool = True
    message: str
    quick_replies: list[str] = Field(default_factory=list, alias="quickReplies")
    logs: list[str] = Field(default_factory=list)
    options: list[dict[str, Any]] = Field(default_factory=list)
    error_code: str | None = Field(default=None, alias="errorCode")
    save: SaveState | None = None
