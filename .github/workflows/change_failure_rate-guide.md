# change_failure_rate.yml 설명 및 실행 방법

이 문서는 GitHub Actions 워크플로 파일인 `change_failure_rate.yml`의 목적, 동작 방식, 실행 방법을 설명합니다.

## 1) 워크플로 목적

이 워크플로는 `deployment_status` 이벤트가 발생할 때 실행되어, 배포 상태가 성공인지 실패인지 로그로 남깁니다.

## 2) 워크플로 내용

```yaml
# 배포 성공/실패 결과 추적
name: Track Deployment Result
on:
  deployment_status:

jobs:
  track-result:
    runs-on: ubuntu-latest
    steps:
      - name: Log Result
        run: |
          STATUS="${{ github.event.deployment_status.state }}"
          # 상태에 따른 로그 분기 처리
          if [ "$STATUS" = "success" ]; then
            echo "✅ Deployment succeeded"
          else
            echo "❌ Deployment failed"
          fi
```

## 3) 구성 항목 설명

- `name: Track Deployment Result`
  - Actions 탭에 표시되는 워크플로 이름입니다.

- `on: deployment_status`
  - 배포 상태 이벤트(예: success, failure)가 발생할 때 실행됩니다.

- `jobs.track-result`
  - 배포 결과를 기록하는 작업입니다.

- `runs-on: ubuntu-latest`
  - GitHub Hosted Ubuntu 러너에서 실행됩니다.

- `steps.Log Result`
  - `github.event.deployment_status.state` 값을 읽어 성공/실패를 분기해 로그를 출력합니다.

## 4) 실행 방법

1. 파일을 아래 경로에 저장합니다.
   - `.github/workflows/change_failure_rate.yml`

2. 배포를 실행하거나 배포 상태 이벤트를 발생시킵니다.
   - 배포 도구 또는 GitHub API를 통해 deployment/deployment_status 이벤트 생성

3. GitHub 저장소의 **Actions** 탭에서 결과를 확인합니다.
   - 워크플로: `Track Deployment Result`
  - 로그: `✅ Deployment succeeded` 또는 `❌ Deployment failed`

## 5) 참고 사항

- 이 워크플로는 배포 실행 자체를 담당하지 않고, 배포 상태를 추적하는 목적입니다.
- 실패 원인 분석을 위해서는 배포를 수행하는 별도 워크플로/서비스 로그를 함께 확인해야 합니다.
