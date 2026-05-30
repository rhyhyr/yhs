# Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

WORKDIR /app

# 의존성 먼저 설치 (캐싱 효율을 위해 requirements.txt 단독 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY agent/ ./agent/
COPY graph_rag/ ./graph_rag/

ENV PYTHONPATH=/app

# 기본 실행 명령 (동작 확인용 smoke test)
CMD ["python", "-c", "print('Visa Navigator container OK')"]
