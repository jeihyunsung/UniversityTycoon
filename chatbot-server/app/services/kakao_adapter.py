from app.models.schemas import GameResult


def to_kakao_response(result: GameResult) -> dict:
    outputs: list[dict] = []

    if result.image_url:
        outputs.append({
            "basicCard": {
                "title": result.image_title or "",
                "description": result.message[:230],
                "thumbnail": {
                    "imageUrl": result.image_url,
                },
            }
        })
    else:
        outputs.append({"simpleText": {"text": result.message}})

    if result.options:
        option_lines = []
        for option in result.options:
            label = option.get("label", "옵션")
            description = option.get("description")
            option_lines.append(f"- {label}" if not description else f"- {label}: {description}")
        outputs.append({"simpleText": {"text": "\n".join(option_lines)}})

    if result.logs:
        outputs.append({"simpleText": {"text": "최근 변화\n" + "\n".join(f"• {log}" for log in result.logs)}})

    return {
        "version": "2.0",
        "template": {
            "outputs": outputs,
            "quickReplies": [
                {
                    "label": label,
                    "action": "message",
                    "messageText": label,
                }
                for label in result.quick_replies
            ],
        },
    }
