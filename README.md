# 🎓 AI RAG for International Students (Capstone Final)
# AI로 작성한 문서입니다 

## 📌 캡스톤 최종 과제 요구사항 체크리스트
| 평가 항목 | 구현 방식 및 링크 |
|---|---|
| **동작 가능한 AI 기능** | `/api/rag` 엔드포인트 구현 완료 (RAG 기반 질의응답) |
| **CI/CD & PR 게이트** | GitHub Actions 린트/테스트 CI 구성 (`.github/workflows/test.yml`) |
| **배포 & 헬스체크** | GCP Cloud Run 기반 무중단 배포 및 `/health` 활성 프로브 설정 |
| **관측성 & 롤백 계획** | API 호출 시 로그 출력(Observability), 에러율 기반 Feature Flag 자동 롤백(`index.js`) |
| **테스트 & 보안** | Jest 단위 테스트 / Playwright E2E 캡처, Dependabot 보안 스캔 적용 |
| **문서화** | `ADR-001.md` (RAG 도입 결정), `RETROSPECTIVE.md` (회고문), 기여 가이드 구성 |

## 🚀 API 사용법
```bash
curl "https://aioss-128796912448.europe-west1.run.app"