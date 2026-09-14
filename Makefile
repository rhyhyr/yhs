# 자주 쓰는 명령 모음. `make help` 로 목록을 봅니다.
.DEFAULT_GOAL := help
.PHONY: help install test lint fmt run ingest front up down logs build clean

help:  ## 사용 가능한 명령을 출력한다
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## 백엔드·프론트 개발 의존성을 설치한다
	cd backend && pip install -e ".[dev]"
	cd frontend && npm ci

test:  ## 백엔드 단위 테스트 (Ollama 필요한 integration 은 제외)
	cd backend && pytest -m "not integration"

lint:  ## 파이썬 + 프론트 린트
	ruff check .
	cd frontend && npm run lint

fmt:  ## 자동 수정 가능한 린트 문제를 고친다
	ruff check --fix .

run:  ## 백엔드 개발 서버 (http://localhost:8000)
	cd backend && uvicorn yhs.api.main:app --reload

front:  ## 프론트 개발 서버 (http://localhost:5173)
	cd frontend && npm run dev

ingest:  ## data/sources 의 PDF 를 Neo4j 지식베이스로 적재한다
	cd backend && yhs --ingest

up:  ## 도커 스택 기동
	docker compose up -d --build

down:  ## 도커 스택 정리
	docker compose down

logs:  ## 백엔드 로그 추적
	docker compose logs -f backend

build:  ## 도커 이미지만 빌드
	docker compose build

clean:  ## 캐시·빌드 산출물 정리
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache backend/coverage.xml frontend/dist
