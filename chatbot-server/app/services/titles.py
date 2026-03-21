from __future__ import annotations

from app.models.schemas import SaveState
from app.services.events import (
    compute_education_power,
    compute_research_power,
    leading_field,
    total_reputation,
)


def compute_dynamic_title(save: SaveState) -> str:
    """Compute a dynamic title for the university based on its current stats.

    Priority order:
    1. Research specialization (laboratory >= 3, research power >= 30)
    2. Education specialization (classroom >= 3, education power >= 40)
    3. Field-specific prestige (leading field reputation >= 30)
    4. Business-oriented (budget >= 1000)
    5. Large university (enrolled >= 200)
    6. Growing (total reputation >= 40)
    7. Default: 작은 대학

    Args:
        save: Current game save state.

    Returns:
        Korean title string for the university.
    """
    research = compute_research_power(save)
    education = compute_education_power(save)
    reputation = total_reputation(save)
    lead = leading_field(save)
    lead_value = getattr(save.reputation, lead)

    # Priority 1: Research specialization
    if research >= 30 and save.buildings.laboratory >= 3:
        return "연구 특화 대학"

    # Priority 2: Education specialization
    if education >= 40 and save.buildings.classroom >= 3:
        return "교육 특화 대학"

    # Priority 3: Field-specific prestige
    field_titles = {
        "arts": "예체능 명문",
        "engineering": "공학 명문",
        "medical": "의학 명문",
        "humanities": "인문 명문",
    }
    if lead_value >= 30 and lead in field_titles:
        return field_titles[lead]

    # Priority 4: Business-oriented
    if save.budget >= 1000:
        return "사업형 대학"

    # Priority 5: Large university
    if save.students.enrolled >= 200:
        return "대규모 대학"

    # Priority 6: Growing
    if reputation >= 40:
        return "성장하는 대학"

    # Priority 7: Default
    return "작은 대학"
