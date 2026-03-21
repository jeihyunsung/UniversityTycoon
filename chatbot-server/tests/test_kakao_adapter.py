from app.models.schemas import GameResult
from app.services.kakao_adapter import to_kakao_response


class TestBasicCardRendering:
    def test_image_url_renders_basic_card(self) -> None:
        result = GameResult(
            message="강의동 건설 완료!",
            imageUrl="https://example.com/img.png",
            imageTitle="🎉 강의동 건설!",
        )
        resp = to_kakao_response(result)
        outputs = resp["template"]["outputs"]
        card = outputs[0]["basicCard"]
        assert card["title"] == "🎉 강의동 건설!"
        assert card["thumbnail"]["imageUrl"] == "https://example.com/img.png"
        assert card["description"] == "강의동 건설 완료!"

    def test_no_image_renders_simple_text(self) -> None:
        result = GameResult(message="현재 상태입니다.")
        resp = to_kakao_response(result)
        outputs = resp["template"]["outputs"]
        assert "simpleText" in outputs[0]
        assert outputs[0]["simpleText"]["text"] == "현재 상태입니다."

    def test_description_truncated_at_230_chars(self) -> None:
        long_msg = "가" * 300
        result = GameResult(
            message=long_msg,
            imageUrl="https://example.com/img.png",
            imageTitle="제목",
        )
        resp = to_kakao_response(result)
        card = resp["template"]["outputs"][0]["basicCard"]
        assert len(card["description"]) == 230

    def test_image_title_none_defaults_to_empty(self) -> None:
        result = GameResult(
            message="테스트",
            imageUrl="https://example.com/img.png",
        )
        resp = to_kakao_response(result)
        card = resp["template"]["outputs"][0]["basicCard"]
        assert card["title"] == ""
