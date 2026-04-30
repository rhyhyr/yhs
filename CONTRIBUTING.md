# Contributing Guide

이 프로젝트에 기여해주셔서 감사합니다! 아래 가이드를 읽고 참여해주세요.

## 기여 방법

### 1. 이슈 먼저 확인

작업 시작 전 [Issues](../../issues) 탭에서 관련 이슈가 있는지 확인하세요. 없다면 새 이슈를 먼저 생성하고 논의 후 작업을 시작합니다.

### 2. 브랜치 생성

`main` 브랜치에서 feature 브랜치를 생성합니다.

```bash
git checkout -b feat/기능명
```

브랜치 네이밍 규칙:

- `feat/` — 새 기능
- `fix/` — 버그 수정
- `docs/` — 문서 수정
- `chore/` — 기타 작업

### 3. 커밋 메시지 규칙 (Conventional Commits)

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
chore: 빌드/설정 변경
test: 테스트 추가/수정
refactor: 코드 리팩터링
```

예시:
```
feat: 하이브리드 검색 점수 가중치 설정 기능 추가
fix: PDF 청킹 오류 수정
```

### 4. Pull Request 생성

- PR 제목도 Conventional Commits 형식을 따릅니다.
- PR 템플릿에 맞게 작성합니다.
- 리뷰어를 최소 1명 지정합니다.

### 5. 코드 리뷰

리뷰어는 `[MUST]` / `[SHOULD]` 태그를 사용해 피드백을 남깁니다.

- `[MUST]` — 반드시 수정이 필요한 사항
- `[SHOULD]` — 권장 사항, 선택적으로 반영 가능

## 개발 환경 설정

```bash
git clone https://github.com/taeing25/yhs_t.git
cd yhs_t
pip install -r requirements.txt
```

환경 변수는 `.env` 파일을 참고하세요.

## 행동 강령

모든 기여자는 [Code of Conduct](CODE_OF_CONDUCT.md)를 준수해야 합니다.

---

> 📝 이 문서는 작성 과정에서 생성형 AI(Claude)의 도움을 받아 작성되었습니다.
