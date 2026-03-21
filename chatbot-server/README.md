# Chatbot Server

카카오 오픈빌더 스킬 서버용 `FastAPI` 골격이다.

## Run

가상환경 생성 후 설치:

```bash
cd chatbot-server
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

개발 서버 실행:

```bash
uvicorn app.main:app --reload
```

헬스 체크:

```bash
curl http://127.0.0.1:8000/health
```

## Current Scope

- 헬스 체크
- 카카오 챗봇용 웹훅 엔드포인트
- 인메모리 저장소 기반 게임 상태 관리
- 상태 조회 / 월 진행 / 건설 / 학과 / 입학 정책 / 로그 조회

DB 연결 전까지는 서버 재시작 시 세이브가 초기화된다.
