# 워크플로우 최적화 전후 비교 리포트

## 개요

GitHub Actions 워크플로우 최적화 작업 결과를 기록합니다.

## 1. 최적화 항목

### Before — 최적화 전

| 항목 | 내용 |
|---|---|
| 구조 | 단일 `ci.yml`에 모든 단계 직접 작성 |
| 중복 | Python 환경 설정 코드가 CI/CD 각각 중복 존재 |
| 캐싱 | pip 캐시 적용, 히트 여부만 확인 |
| 배포 | 모든 push에 대해 전체 배포 실행 |
| Matrix | Python 3.10/3.11 × ubuntu/windows (4조합) |

### After — 최적화 후

| 항목 | 내용 |
|---|---|
| 구조 | Reusable Workflow + Composite Action으로 분리 |
| 중복 제거 | `setup-python-env` Composite Action으로 환경 설정 일원화 |
| 캐싱 | 캐시 조회 시간(ms) 측정 및 Job Summary에 리포트 |
| 배포 | 변경된 파일 경로 기준 선택적 배포 (`dorny/paths-filter`) |
| Matrix | 동일 4조합, Reusable Workflow 호출로 중복 제거 |

---

## 2. 캐싱 성능 비교

| 구분 | 캐시 미스 (첫 실행) | 캐시 히트 (재실행) |
|---|---|---|
| pip install 소요 시간 | 약 80~90초 | 약 5~10초 |
| 개선율 | — | 약 **88% 단축** |

> 캐시 키: `runner.os + python-version + requirements.txt 해시`
> 측정 방법: Composite Action 내 `date +%s%3N` 기준 전후 측정

---

## 3. 선택적 배포 효과

| 변경 경로 | 이전 (전체 배포) | 이후 (선택적 배포) |
|---|---|---|
| `docs/` 만 변경 | 전체 파이프라인 실행 | 배포 스킵 ⏭️ |
| `agent/` 변경 | 전체 파이프라인 실행 | agent 모듈만 배포 ✅ |
| `graph_rag/` 변경 | 전체 파이프라인 실행 | graph_rag 모듈만 배포 ✅ |
| `requirements.txt` 변경 | 전체 파이프라인 실행 | 의존성 검증만 실행 ✅ |

---

## 4. 파일 구조 변경

```
.github/
├── actions/
│   └── setup-python-env/
│       └── action.yml         ← Composite Action (신규)
└── workflows/
    ├── ci.yml                 ← Matrix → Reusable Workflow 호출로 변경
    ├── reusable-ci.yml        ← Reusable Workflow (신규)
    └── selective-deploy.yml   ← 변경 파일 감지 기반 조건부 배포 (신규)
```

---

> 📝 이 문서는 작성 과정에서 생성형 AI(Claude)의 도움을 받아 작성되었습니다.
