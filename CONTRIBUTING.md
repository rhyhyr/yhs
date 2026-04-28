# Contributing Guide

이 문서는 `yhs` 저장소에 기여할 때 따라야 할 협업 규칙을 정리합니다.
처음 PR을 올리기 전에 한 번 훑어 봐주세요.

---

## 1. 브랜치 전략 (GitHub Flow)

본 저장소는 **GitHub Flow**를 따릅니다.

```
main  ────●────────────●────────────●─── (항상 배포 가능)
           \           /\           /
            \─feat/A──/  \─fix/B───/
```

- `main`은 **항상 배포 가능한 상태**를 유지합니다.
- 모든 작업은 `main`에서 분기한 **feature 브랜치**에서 진행합니다.
- 작업이 끝나면 PR을 통해 `main`으로 머지합니다.
- `main`으로의 직접 push는 금지됩니다 (브랜치 보호 규칙).

### 브랜치 네이밍

| 종류 | 예시 |
|---|---|
| 기능 | `feat/login-page`, `feat/week4-github-flow` |
| 버그 | `fix/crawler-timeout` |
| 문서 | `docs/contributing-guide` |
| 리팩터링 | `refactor/agent-runtime` |
| 테스트 | `test/regression-cases` |
| 잡일 | `chore/update-deps` |

> 짧고 의미 있는 이름을 사용하세요. 한글/공백/특수문자는 피합니다.

---

## 2. 커밋 메시지 — Conventional Commits

```
<type>(<scope>): <subject>

<body>          # 선택, 무엇을 / 왜 바꿨는지
<footer>        # 선택, BREAKING CHANGE / Closes #123
```

### 사용 가능한 type

| type | 의미 |
|---|---|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 포맷, 세미콜론 등 동작 변경 없는 스타일 |
| `refactor` | 리팩터링 (동작 변경 없음) |
| `perf` | 성능 개선 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정, 의존성 등 |

### 좋은 예시

```
feat(crawler): 응답 캐싱 기능 추가
fix(agent): 컨텍스트 토큰 초과 오류 수정
docs(readme): 설치 가이드 보강
refactor(rag): 검색 함수를 모듈로 분리
```

### 나쁜 예시

```
update                       ❌ 무엇을 했는지 모름
버그 수정함                   ❌ type/scope 없음
feat: 이거저거 다 바꿈        ❌ 한 PR에 여러 주제
```

---

## 3. PR (Pull Request) 절차

### 작업 시작

```bash
git checkout main
git pull origin main
git checkout -b feat/my-feature
```

### 작업 중

- 작은 단위로 자주 커밋합니다 (한 커밋 = 한 가지 변경).
- 한 PR은 **하나의 주제**만 다룹니다.

### PR 올리기 전 체크

```bash
git fetch origin
git rebase origin/main          # 또는 git merge origin/main
# 충돌 해결 후
git push origin feat/my-feature
```

### PR 본문

저장소의 **PR 템플릿**을 그대로 사용합니다.
- 변경 사항 요약 / 작업 유형 / 관련 이슈 / 테스트 방법 / 체크리스트
- 제목은 Conventional Commits 형식.

### 리뷰

- **최소 1명의 Approve** 후 머지 가능.
- `[MUST]`로 표시된 코멘트는 **반드시 반영**하거나 합의된 후에 머지.
- 자세한 리뷰 규칙은 [`docs/REVIEW_GUIDE.md`](docs/REVIEW_GUIDE.md) 참고.

### 머지 방식

- **Squash and merge**를 기본으로 합니다 (히스토리가 깔끔해집니다).
- 머지된 feature 브랜치는 삭제합니다.

---

## 4. 이슈 작성

- 버그 리포트: `.github/ISSUE_TEMPLATE/bug_report.md`
- 기능 제안: `.github/ISSUE_TEMPLATE/feature_request.md`

이슈에 라벨(`bug`, `enhancement`, `documentation` 등)을 붙여 주세요.

---

## 5. 보안 / 비밀 정보

- API 키, 비밀번호, 토큰을 **절대 커밋하지 마세요**.
- 환경 변수(`.env`)는 `.gitignore`에 포함되어 있습니다.
- 실수로 커밋했다면 즉시 키를 폐기하고 새로 발급받으세요.

---

## 6. 도움 요청

막히면 언제든 이슈를 열거나, PR에 `[Q]` 태그로 코멘트를 남겨 주세요.

Happy Coding!