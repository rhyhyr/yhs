# DORA 지표 결과

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
| Deployment Frequency | `TBD` | [.github/workflows/deployment.yml](.github/workflows/deployment.yml) | 간단한 해석을 작성 |
| Lead Time for Changes | `TBD` | [.github/workflows/lead-time.yml](.github/workflows/lead-time.yml), `metrics.yml` | 간단한 해석을 작성 |
| Change Failure Rate | `TBD` | [.github/workflows/change_failure_rate.yml](.github/workflows/change_failure_rate.yml) | 간단한 해석을 작성 |
| Mean Time to Restore | `TBD` | [.github/workflows/mttr-monitoring.yml](.github/workflows/mttr-monitoring.yml), `mttr-metrics.json` | 워크플로가 실행되면 MTTR 계산 결과를 `mttr-metrics.json`으로 생성하고 아티팩트로 업로드합니다. |

## DORA 차트

### Deployment Frequency

![Deployment Frequency](./images/dora/deployment-frequency.png)

### Lead Time for Changes

![Lead Time for Changes](./images/dora/lead-time-for-changes.png)

### Change Failure Rate

![Change Failure Rate](./images/dora/change-failure-rate.png)

### Mean Time to Restore

![Mean Time to Restore](./images/dora/mean-time-to-restore.png)

## 참고

- 가능하면 이미지 크기를 통일하세요.
- 차트 제목은 위 지표 이름과 맞춰서 사용하세요.
- 추가 관찰 사항이나 특이사항은 아래에 적어주세요.
- 지표별 실제 수집/기록 파일은 위 표의 파일 위치를 참고하세요.

## 부록

- 원본 데이터 출처:
- 분석 날짜:
- 담당자:
