# Troubleshooting

이 페이지는 설치나 실행 중 자주 생기는 문제를 해결하는 데 도움을 줍니다.

## 자주 발생하는 문제

## 1) `ModuleNotFoundError`

### 원인

현재 활성화된 Python 환경에 의존성이 설치되지 않았습니다.

### 해결 방법

```bash
pip install -r requirements.txt
```

그다음 애플리케이션을 다시 실행합니다.

## 2) API key 또는 credential 오류

### 원인

필요한 환경 변수가 없거나 값이 잘못되었습니다.

### 해결 방법

- 환경 변수 이름이 맞는지 확인합니다.
- 값을 수정한 뒤에는 터미널이나 세션을 다시 시작합니다.

## 3) 시작은 되지만 동작이 이상한 경우

### 원인

인덱스나 캐시된 산출물이 오래되어 현재 상태와 맞지 않을 수 있습니다.

### 해결 방법

- 인덱스 산출물을 다시 생성합니다.
- regression 시나리오를 다시 실행합니다.

## 점검 순서

1. [[Getting Started]] / [Getting Started](Getting%20Started.md)로 설치 상태를 먼저 확인합니다.
2. [[Development Guide]] / [Development Guide](Development%20Guide.md)의 작업 흐름과 검증 단계를 다시 봅니다.
3. 최소 입력으로 재현해 보고 로그를 비교합니다.

## 관련 문서

- [[Home]] / [Home](Home.md)
- [[Getting Started]] / [Getting Started](Getting%20Started.md)
- [[Development Guide]] / [Development Guide](Development%20Guide.md)
