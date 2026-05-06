# deployment.yml 설명 및 사용법

이 문서는 GitHub Actions 워크플로 파일인 `deployment.yml`의 동작 방식과 사용 방법을 설명합니다.

## 1) 워크플로 목적

이 워크플로는 GitHub에서 `deployment` 이벤트가 발생할 때 실행되며, 다음 정보를 로그로 출력합니다.

- 배포 실행 시각 (`date`)
- 배포 대상 환경 (`github.event.deployment.environment`)

## 2) 워크플로 내용

```yaml
# GitHub Actions로 배포 빌드 추적
name: Track Deployments
on:
  deployment:

jobs:
  track-deployment:
    runs-on: ubuntu-latest
    steps:
      - name: Log Deployment
        run: |
          echo "Deployment at: $(date)"
          echo "Environment: ${{ github.event.deployment.environment }}"
```

## 3) 각 항목 설명

- `name: Track Deployments`
  - GitHub Actions 탭에 표시되는 워크플로 이름입니다.

- `on: deployment`
  - 배포 이벤트가 생성될 때 이 워크플로를 트리거합니다.

- `jobs.track-deployment`
  - 실제 실행 단위(job)입니다.

- `runs-on: ubuntu-latest`
  - GitHub가 제공하는 Ubuntu 러너에서 실행합니다.

- `steps > Log Deployment`
  - 셸 명령으로 배포 시간과 환경 정보를 출력합니다.

## 4) 사용 방법

1. 워크플로 파일을 저장합니다.
   - 경로: `.github/workflows/deployment.yml`

2. GitHub에서 배포 이벤트를 발생시킵니다.
   - 예: GitHub API 또는 배포를 생성하는 자동화 도구 사용

3. 저장소의 **Actions** 탭에서 실행 결과를 확인합니다.
   - `Track Deployments` 워크플로 실행 기록 확인
   - 로그에서 `Deployment at`, `Environment` 출력 확인

## 5) 참고 사항

- 이 워크플로는 **배포 자체를 수행하지 않고**, 배포 이벤트를 **추적/기록**하는 용도입니다.
- 배포 이벤트에 `environment` 값이 없으면 환경명이 비어 보일 수 있습니다.
