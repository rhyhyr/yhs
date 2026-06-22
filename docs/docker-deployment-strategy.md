# Docker 기반 배포 파이프라인 전략

## 브랜치별 이미지 태깅 전략

| 브랜치 | 이미지 태그 | 용도 |
|--------|------------|------|
| `feature/*` | `sha-{commit}` | 개발/테스트 |
| `main` | `latest`, `sha-{commit}` | 스테이징 |
| `v*` 태그 | `{semver}` (예: `1.2.3`) | 프로덕션 |

## 파이프라인 단계

```
[1] Build      → Dockerfile 기반 이미지 빌드
[2] Smoke Test → docker run으로 컨테이너 정상 기동 확인
[3] Push       → ghcr.io (GitHub Container Registry) 업로드
[4] Deploy     → AWS Lambda / GCP Cloud Run / 자체 서버
[5] Health     → /health 엔드포인트 응답 확인
[6] Rollback   → 헬스체크 실패 시 이전 태그로 자동 전환
```

## 환경별 배포 흐름

```
개발자 push
  └→ CI (lint + test)
       └→ Docker build & push (sha 태그)
            └→ 스테이징 자동 배포 (main 태그)
                 └→ 수동 승인
                      └→ 프로덕션 배포 (semver 태그)
```

## 롤백 전략

- 프로덕션 배포 후 5분간 헬스체크 모니터링
- 실패 감지 시 직전 안정 태그로 즉시 재배포
- GitHub Actions의 `if: failure()` 스텝으로 자동화
