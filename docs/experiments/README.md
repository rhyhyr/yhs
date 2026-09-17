# 평가 실험

이 폴더는 **문서**만 있다. 실제 코드와 데이터셋은 저장소 루트의
[experiments/](../../experiments/) 에 있다.

| 문서 | 내용 |
|---|---|
| [실행계획.md](실행계획.md) | N=100 측정 절차 — 사전점검 → 워밍업 → 러너 → 채점 → 집계 |
| [프로토콜.md](프로토콜.md) | 질문셋 설계, LLM-as-judge 루브릭, feature flag ablation, 발표 수치 사실관계 정정 |

## 코드

```
experiments/
├── eval_sets/            질문셋 (eval_questions_v2.py, v3.py)
├── run_eval100.py        답변 수집 러너 — Ollama
├── run_eval100_openai.py 답변 수집 러너 — OpenAI
├── run_eval_uncovered.py 미수록 질문(크롤러 폴백) 전용
├── zh_eval.py            중국어 질문 평가
├── make_judge_prompt.py  LLM-as-judge 프롬프트 생성
├── metrics.py            지표 계산
├── show_metrics.py       결과 요약 출력
├── generate_report.py    리포트 생성
├── compare_results.py    실행 간 비교
├── threshold_sweep.py    문턱값 스윕
├── weight_sweep_optuna.py 재랭크 가중치 Optuna 스윕
└── results/              실행 결과 (git 제외)
```

## 실행

저장소 루트에서 돌린다 (`experiments.*` 패키지 import 때문).

```bash
python experiments/run_eval100_openai.py
python experiments/weight_sweep_optuna.py
```

`retrieval.yaml` 의 가중치를 바꿨다면 `weight_sweep_optuna.py` 로 재검증한다.
일시적으로 값을 덮어쓸 때는 환경변수를 쓴다:

```bash
TOP_K_VECTOR=8 GATE_MIN_TOP_SCORE=0.3 python experiments/run_eval100_openai.py
```

## 정직성 규칙

- 발표·보고서에는 **실제 N** 을 그대로 쓴다.
- stratum 별 N 이 작은 칸은 비율에 실제 개수를 병기한다 — "75% (9/12)".
- 답변 모델과 심판 모델은 반드시 분리한다.
- 예전 측정값(Gemini·in-DB 기준)과 새 측정값을 직접 비교하지 않는다.
