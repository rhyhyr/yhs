# Development Guide

이 페이지는 코드베이스를 안전하고 일관되게 수정하는 방법을 설명합니다.

## 프로젝트 구조

- `main.py`: 애플리케이션 진입점
- `agent_runtime.py`: 실행 흐름 조율
- `indexing/`: 인덱싱 파이프라인과 모델
- `regression_test.py`: 기준 동작 검증 흐름

## 개발 흐름

1. `main`에서 기능 브랜치를 만듭니다.
2. 작은 단위로 집중된 커밋을 남깁니다.
3. 푸시 전에 로컬 점검을 실행합니다.
4. Pull Request를 열고 리뷰를 요청합니다.

## 로컬 검증

- 먼저 의존성을 설치합니다.
- 기본 실행 경로를 확인합니다.

  ```bash
  python main.py
  ```

- 검색이나 인덱싱 동작을 바꿀 때는 regression 체크를 함께 실행합니다.

## 개발 중 문제 해결

- 실행 오류나 의존성 문제: [[Troubleshooting]] / [Troubleshooting](Troubleshooting.md)
- 처음 환경을 구성할 때: [[Getting Started]] / [Getting Started](Getting%20Started.md)

## 관련 문서

- [[Home]] / [Home](Home.md)
- [[Getting Started]] / [Getting Started](Getting%20Started.md)
- [[Troubleshooting]] / [Troubleshooting](Troubleshooting.md)
