# YHS 실험 폴더

발표용 평가 실험에 필요한 것들을 모아둔 폴더.

## 파일
| 파일 | 역할 |
|------|------|
| `YHS_실험_실행계획.md` | ★메인★ Claude Code에 주는 실행 프로토콜 (사전점검→워밍업→러너→채점→집계) |
| `YHS_eval_questions_100.py` | 검증셋 100문항 (질문+gold+출처). `EVAL_QUERIES` |
| `YHS_eval_metrics.py` | 100문항에 6지표용 태그 부여 + 최신성 쌍. `EVAL`, `FRESHNESS_PAIRS` |
| `eval_harness.py` | 채점 하니스 골격(드라이런 가능). 실측은 프로토콜대로 러너 작성 권장 |
| `YHS_eval_questions_seed.py` | 초기 시드 24문항 (참고용, 100의 모태) |
| `YHS_실험_프로토콜.md` | 이전 상세 프로토콜 (N=40·4단계 버전, 참고용) |
| `_dryrun_샘플/` | 드라이런(목) 출력 예시 — 실제 결과 아님. 무시해도 됨 |

## 실행 메모
- **실제 실험은 레포 루트에서 실행** (`experiments.*` 패키지 import 때문).
  러너가 `backend/src` 를 sys.path 에 넣어 주므로 `pip install -e backend` 없이도 동작한다.
  예: 루트에서 `python -m 실험.eval_harness` 또는 러너를 `experiments/`에 두고 실행.
- 드라이런(스택 없이 하니스 점검)은 이 폴더 안에서: `python eval_harness.py dry`
- 확정안: 답변=EXAONE / 심판=gpt-4o-mini / N=100 / A안(단일 측정).

자세한 절차는 `YHS_실험_실행계획.md` 참고.
