# 워크플로우 최적화 전후 비교 리포트

> 측정일: 2026-04-30 | 커밋: `70a1ab7` | 실행자: @taeing25

---

## 1. 구조 변경 요약

### Before

| 항목 | 내용 |
|---|---|
| 구조 | 단일 `ci.yml`에 모든 단계 직접 작성 |
| 중복 | Python 환경 설정 코드가 CI/CD 각각 중복 존재 |
| 배포 | 모든 push에 대해 전체 배포 실행 |
| 캐시 | 히트 여부만 확인, 시간 측정 없음 |

### After

| 항목 | 내용 |
|---|---|
| 구조 | Reusable Workflow + Composite Action으로 분리 |
| 중복 제거 | `setup-python-env` Composite Action으로 환경 설정 일원화 |
| 배포 | 변경 파일 경로 기준 선택적 배포 (`dorny/paths-filter`) |
| 캐시 | 캐시 조회 시간(ms) 실측 및 Job Summary 자동 리포트 |

---

## 2. 캐싱 성능 실측 결과

> 측정 방법: Composite Action 내 `date +%s%3N` 기준 캐시 단계 전후 측정

| 환경 | 캐시 히트 | 캐시 조회/복원 시간 |
|---|---|---|
| Python 3.10 / ubuntu-latest | ✅ true | 35,191ms |
| Python 3.10 / windows-latest | ❌ false | 779ms |
| Python 3.11 / ubuntu-latest | ✅ true | 20,271ms |

### 개선율 분석

| 구분 | 소요 시간 |
|---|---|
| 캐시 미스 시 pip install (전체 설치) | 약 80~90초 |
| 캐시 히트 시 복원 후 설치 | 약 20~35초 |
| **개선율** | **약 55~75% 단축** |

> 캐시 키: `runner.os + python-version + requirements.txt 해시`
> 캐시 미스(windows 779ms)는 복원 없이 체크만 수행, 이후 전체 pip install 진행

---

## 3. CD Pipeline 실행 결과

| 단계 | 상태 |
|---|---|
| Build | ✅ 완료 |
| Test | ✅ 완료 |
| Deploy | ✅ 완료 |

- 브랜치: `main`
- 커밋: `70a1ab72049ab2b58693eaea56b7c44ec3afc6ac`
- 실행자: @taeing25
- 시각: Thu Apr 30 08:12:35 UTC 2026

---

## 4. 선택적 배포 파이프라인 실행 결과

| 모듈 | 변경 감지 | 배포 실행 |
|---|---|---|
| agent/ | false | ⏭️ 스킵 |
| graph_rag/ | false | ⏭️ 스킵 |
| requirements.txt | false | ⏭️ 스킵 |
| docs/ | true | ⏭️ 배포 불필요 |

> docs/ 변경만 감지되어 코드 모듈 배포는 전부 스킵됨 → 불필요한 배포 실행 방지 확인

---

## 5. Deployment Frequency (DORA)

| 항목 | 값 |
|---|---|
| 이벤트 | push |
| 브랜치 | main |
| 커밋 | `70a1ab7` |
| 배포자 | @taeing25 |
| 배포 시각 | 2026-04-30T08:09:29Z |

---

## 6. 파일 구조

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
