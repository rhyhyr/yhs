#ai로 생성한 문서입니다

# DORA 지표 결과 및 7,8 주차 과제

이 문서는 DORA 지표 결과 이미지를 넣기 위한 자리표시자 구조입니다.
아래 이미지 경로를 생성한 차트나 스크린샷 경로로 바꿔서 사용하세요.

## 개요

- 프로젝트: `yhs`
- 보고 날짜: `2026-04-29`
- 대상 워크플로: `workflows/`

## 요약

현재 전달 성과에 대한 간단한 요약을 작성하세요.

| Metric | 값 | 파일 위치 | 설명 |
| --- | --- | --- | --- |
| Deployment Frequency | `높음 (최근 지속 실행)` | [.github/workflows/deployment.yml](.github/workflows/deployment.yml) | 최근 Track Deployments 실행 이력이 연속적으로 관찰되고 모두 성공 상태여서, 배포가 끊기지 않고 자주 수행되는 편으로 해석할 수 있습니다. 실행 소요 시간도 대체로 짧아(약 5~12초) 배포 추적 파이프라인은 안정적으로 동작 중입니다. |
| Lead Time for Changes | `안정적 (최근 4회 연속 성공)` | [.github/workflows/lead-time.yml](.github/workflows/lead-time.yml), `metrics.yml` | 최근 PR이 닫힐 때마다 워크플로가 실행되었고 4회 모두 성공했습니다. 실행 시간도 약 6~7초로 짧아서, 변경 후 리드 타임을 기록하는 파이프라인이 안정적으로 동작하고 있다고 볼 수 있습니다. |
| Change Failure Rate | `수동 실행 성공` | [.github/workflows/change_failure_rate.yml](.github/workflows/change_failure_rate.yml) | `Track Deployment Result`를 수동 실행했을 때 `Deployment succeeded` 로그가 정상 출력되어, 배포 결과를 성공으로 기록하는 흐름은 정상입니다. 현재 화면만 보면 실패 사례는 없어서 실제 실패율 수치보다는 성공 추적 상태를 확인한 결과로 해석할 수 있습니다. |
| Mean Time to Restore | `실행 성공 (약 7초)` | [.github/workflows/mttr-monitoring.yml](.github/workflows/mttr-monitoring.yml), `mttr-metrics.json` | `Generate MTTR metrics`와 `Upload MTTR metrics` 단계가 정상 완료되어 지표 파일 생성/업로드 흐름은 정상입니다. 다만 실행 경고 1건이 있어 사용 액션 런타임(예: Node.js 버전) 호환성 점검이 필요합니다. |

## DORA 차트

### Deployment Frequency

![Deployment Frequency] ![alt text](deployment_frequency.png)

### Lead Time for Changes

![Lead Time for Changes] ![alt text](lead_time.png)

### Change Failure Rate

![Change Failure Rate] ![alt text](change_failure_rate.png)

### Mean Time to Restore!

![Mean Time to Restore] ![alt text](mttr_monitoring.png)


🚀 GitHub Actions Optimization Project본 프로젝트는 GitHub Actions의 고급 기능을 활용하여 CI/CD 파이프라인의 중복을 제거하고, 캐싱 전략을 통해 실행 속도를 혁신적으로 개선한 사례를 다룹니다.🛠️ Key Implementation1. 효율적인 자동화 구조 설계Matrix Strategy: 다중 환경(Ubuntu Latest) 및 다양한 언어 버전(Python 3.10, 3.11, 3.12)에 대한 확장 테스트를 자동화했습니다.Modularization: Reusable Workflow 및 Composite Action을 설계하여 워크플로우 간 중복 코드를 제거하고 유지보수성을 극대화했습니다.2. 지능형 파이프라인 제어Selective Deployment: 브랜치/PR 조건부 실행 및 변경 파일 감지(Path Filtering)를 적용하여 불필요한 빌드를 방지하고 리소스를 절약합니다.Execution Monitoring: 작업 실행 시간을 실시간으로 측정하여 최적화 성과를 데이터로 기록합니다.📈 Performance Optimization Report패키지 설치 단계에서 Dependency Caching을 적용하기 전(Cold)과 후(Cached)의 성능을 비교 분석한 결과입니다.OSEnvironmentCold InstallCached InstallImprovementubuntu-latestPython 3.1092.174s76.21s17.32%ubuntu-latestPython 3.1182.655s67.083s18.84%ubuntu-latestPython 3.12146.87s89.56s39.02%Analysis Summary: Python 3.12 환경에서 최대 **39.02%**의 성능 향상을 기록했으며, 전반적으로 캐싱 도입 후 빌드 시간이 유의미하게 단축되었습니다.🔗 Action Resources상세한 실행 로그와 결과 리포트는 아래 링크에서 확인하실 수 있습니다.GitHub Run History: View Workflow RunOptimization Artifacts:Python 3.10 ReportPython 3.11 ReportPython 3.12 Report📂 Project StructurePlaintext.github/
├── workflows/
│   ├── main.yml           # 메인 파이프라인 (Selective Deployment 적용)
│   └── reusable-test.yml  # Reusable Workflow
└── actions/
    └── setup-env/         # Composite Action

