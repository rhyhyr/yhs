# -*- coding: utf-8 -*-
"""
YHS 평가 데이터셋 — 6개 지표 측정용 재구조화

기존 100문항(YHS_eval_questions_100.EVAL_QUERIES)을 import해서 지표 태그를 붙이고,
지표 측정에 빠져 있던 조각(계산문항·최신성 버전쌍)을 추가한다.
모든 query/gold/source 근거는 데이터베이스보강방향.md.

────────────────────────────────────────────────────────────
측정할 6개 지표 ↔ 데이터셋에서 쓰는 부분 ↔ 계산식
────────────────────────────────────────────────────────────
① 근거 적합률 (grounding rate)
   대상: grounding_evaluable=True 인 문항 (uncovered/크롤러 제외)
   계산: 사람이 '근거가 결론을 지지하는가(Y/N)' 체크 → Yes 비율
② 근거 커버리지 (citation coverage)
   대상: multi_claim=True 인 문항 (여러 주장이 든 답변)
   계산: 답변을 문장 단위로 분해 → 핵심주장 문장 중 출처가 붙은 비율
③ 최신성 정답률 (freshness accuracy)
   대상: FRESHNESS_PAIRS (구버전 vs 신버전 근거를 섞어 A/B)
   계산: 최신 근거(newest)를 우선 인용/선택한 비율
④ 지연시간 (latency)
   대상: latency_type 별로 분리 — repeated / long_tail / calculation / standard
   계산: 각 유형 p50 / p95 응답시간 (같은 query 반복 실행해 분포 측정)
⑤ 비용·캐시 히트율 (cost & cache hit)
   대상: cache_cluster 가 같은 문항들(같은 gold, 다른 표현)
   계산: 1,000건당 검색/리랭킹/LLM 비용 + 클러스터 2번째 이후 질의의 캐시 히트율
⑥ 답변 완전성 (completeness)
   대상: completeness_checklist 가 있는 문항
   계산: 체크리스트 항목 중 답변에 실제 포함된 비율 (= 1 - 누락률)

추가된 필드(각 문항):
   metrics                : 이 문항이 기여하는 지표 목록
   grounding_evaluable    : ① 대상 여부 (uncovered=False)
   multi_claim            : ② 대상 여부
   latency_type           : ④ 유형 (repeated/long_tail/calculation/standard)
   cache_cluster          : ⑤ 클러스터 id (같으면 같은 답의 다른 표현)
   completeness_checklist : ⑥ 답변에 반드시 들어가야 할 항목 리스트

⚠️ '계산(calculation)' 문항 주의: YHS가 산술을 실제로 하는지 확인 필요.
   하지 않으면 이 문항들은 '다중 근거 종합(aggregation)' 지연/완전성 테스트로 해석.
"""

from YHS_eval_questions_100 import (
    EVAL_QUERIES as _BASE,
    S_REGTIME, S_DONGAVISA, S_CHGSTATUS, S_STUDYKR, S_NHISDISC,
    S_IMMARREAR, S_KOTRATEL, S_BANKGUIDE, S_NHISLAW, S_MANUAL,
    S_BANKNEWS, S_ENROLL, S_BUSANSUP,
)

# ── ⑤ 캐시 클러스터: 같은 gold를 다른 표현(ko오타/zh/en/구어)으로 묻는 묶음 ──
#    (2번째 이후 질의에서 캐시 히트가 나야 정상. 필요하면 멤버를 4~5개로 늘리면 됨)
_CACHE_CLUSTERS = {
    "reg_deadline":      ["v_indb_1", "v_dirty_1"],
    "ext_apply":         ["v_indb_6", "v_dirty_2"],
    "change_d4d2":       ["v_indb_4", "v_dirty_3"],
    "ins_discount":      ["i_indb_3", "i_dirty_1"],
    "ins_arrears":       ["i_cplx_3", "i_dirty_2"],
    "ins_start":         ["i_indb_2", "i_dirty_3"],
    "work_confirm":      ["w_indb_5", "w_dirty_1"],
    "work_nopermit":     ["w_cplx_1", "w_dirty_2"],
    "work_construction": ["w_cplx_3", "w_dirty_3"],
    "dorm_room":         ["h_indb_2", "h_dirty_1"],
    "bank_noarc":        ["b_indb_2", "b_dirty_1"],
    "phone_postpaid":    ["t_indb_2", "t_dirty_1"],
    "sim_prepaid":       ["t_indb_1", "t_dirty_2"],
}
_ID2CLUSTER = {qid: cl for cl, ids in _CACHE_CLUSTERS.items() for qid in ids}

# ── ④ '반복(repeated)' 으로 분류할 고빈도 FAQ (반복 실행 → 캐시·지연 측정) ──
_REPEATED = {"v_indb_1", "v_indb_6", "w_indb_1", "i_indb_3",
             "h_indb_1", "sp_indb_1", "ac_indb_4", "b_indb_1"}

# ── ② multi_claim=True (복수 주장/목록형 답변) 으로 강제 지정할 in_db 문항 ──
_MULTI_CLAIM = {"v_indb_2", "v_indb_5", "v_indb_7", "v_indb_10",
                "w_indb_2", "w_indb_3", "b_indb_1", "t_indb_2"}

# ── ⑥ 완전성 체크리스트 (답변에 반드시 포함돼야 할 항목) ──
_CHECKLISTS = {
    "v_indb_2":  ["통합신청서", "여권", "사진", "재학증명서"],
    "v_indb_5":  ["신청서", "사진", "여권사본", "외국인등록증", "체류지입증",
                  "잔고증명", "학력입증서류", "어학연수 출석증명", "등록금 납부증명"],
    "v_indb_7":  ["통합신청서", "여권", "외국인등록증", "체류지 입증서류", "수수료"],
    "v_indb_10": ["통합신청서/사진", "외국인등록증", "여권사본", "재학증명서",
                  "성적증명서", "체류지 입증서류", "수수료"],
    "w_indb_2":  ["근로계약서", "학교 확인서", "하이코리아/출입국 신청", "허가 후 근무"],
    "w_indb_3":  ["여권", "외국인등록증", "통합신청서", "시간제취업 확인서",
                  "성적/출석 증명", "한국어 능력 증빙", "사업자등록증 사본", "표준근로계약서"],
    "b_indb_1":  ["여권", "외국인등록증", "국내 주소", "연락처",
                  "재학증명서/입학허가서", "금융거래 목적 확인서류"],
    "t_indb_2":  ["외국인등록증/거소신고증", "본인 명의 통장·카드"],
}


def _enrich(q):
    q = dict(q)
    st = q["stratum"]
    qid = q["id"]
    q["grounding_evaluable"] = (st != "uncovered")
    if st == "uncovered":
        q["latency_type"] = "long_tail"
    elif qid in _REPEATED:
        q["latency_type"] = "repeated"
    else:
        q["latency_type"] = "standard"
    q["cache_cluster"] = _ID2CLUSTER.get(qid)
    q["multi_claim"] = (st == "complex") or (qid in _MULTI_CLAIM)
    q["completeness_checklist"] = _CHECKLISTS.get(qid)
    m = []
    if q["grounding_evaluable"]:
        m.append("grounding")
    if q["multi_claim"]:
        m.append("citation")
    if q["completeness_checklist"]:
        m.append("completeness")
    if q["cache_cluster"]:
        m.append("cache")
    if q["latency_type"] != "standard":
        m.append("latency")
    q["metrics"] = m
    return q


# ── ④ 계산/종합(aggregation) 문항 — 기존 셋에 없던 유형 추가 ──
_CALC = [
    {"id": "calc_1", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "성적이 1.8이고 초과학기인데 D-2 연장하려면 서류를 다 합쳐서 뭐가 필요해?",
     "expected_intent": "visa",
     "gold": "기본: 통합신청서/사진, 외국인등록증, 여권사본, 재학증명서, 성적증명서, 체류지 입증서류, 수수료. "
             "추가(2.0 미만·초과학기·졸업유예): 은행잔고증명, 사유서, 지도교수 확인서. 최종은 출입국 판단.",
     "source": S_DONGAVISA,
     "completeness_checklist": ["통합신청서/사진", "외국인등록증", "여권사본", "재학증명서", "성적증명서",
                                "체류지 입증서류", "수수료", "은행잔고증명", "사유서", "지도교수 확인서"]},
    {"id": "calc_2", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "어학연수 끝나고 대학원 합격했는데 출국 안 하고 다니려면 절차랑 서류 다 알려줘",
     "expected_intent": "visa",
     "gold": "절차: 체류자격 변경허가를 새 활동(유학) 시작 전 국내 관할 출입국관서에서 받음. "
             "서류: 신청서, 사진, 여권사본, 외국인등록증, 체류지 입증, 잔고증명, 학력입증서류, 어학연수 출석증명, 등록금 납부증명.",
     "source": S_CHGSTATUS,
     "completeness_checklist": ["변경허가(활동 전 신청)", "신청서", "사진", "여권사본", "외국인등록증",
                                "체류지 입증", "잔고증명", "학력입증서류", "어학연수 출석증명", "등록금 납부증명"]},
    {"id": "calc_3", "lang": "ko", "category": "work", "stratum": "complex",
     "query": "아르바이트 처음 하는데 허가까지 단계별로 다 알려줘",
     "expected_intent": "work",
     "gold": "절차: 근로계약서 작성 → 학교 유학생 담당자 확인서 → 하이코리아 온라인/출입국 방문 신청 → 허가 후 근무. "
             "서류: 여권, 외국인등록증, 통합신청서, 시간제취업 확인서, 성적/출석 증명, 한국어 증빙, 사업자등록증 사본, 표준근로계약서.",
     "source": S_STUDYKR,
     "completeness_checklist": ["근로계약서", "학교 확인서", "하이코리아/출입국 신청", "허가 후 근무",
                                "여권", "외국인등록증", "시간제취업 확인서", "한국어 증빙", "표준근로계약서"]},
    {"id": "calc_4", "lang": "ko", "category": "insurance", "stratum": "complex",
     "query": "건강보험 50% 경감받는데 보험료가 밀리면 비자까지 어떻게 이어져?",
     "expected_intent": "health_insurance",
     "gold": "D-2/D-4는 지역가입 50% 경감 대상이지만, 미납 시 급여 제한·체납처분이 있고 "
             "체류기간 연장 신청 때 체납이 확인되면 원칙적으로 6개월 이하로 제한 연장될 수 있음.",
     "source": S_IMMARREAR,
     "completeness_checklist": ["50% 경감 대상", "미납 시 급여 제한", "연장 시 체납 확인", "원칙 6개월 이하 제한 연장"]},
    {"id": "calc_5", "lang": "ko", "category": "admin", "stratum": "complex",
     "query": "입국하자마자 외국인등록부터 통장·핸드폰까지 순서대로 뭘 해야 해?",
     "expected_intent": "visa",
     "gold": "① 외국인등록(90일 초과 체류 시 입국일부터 90일 이내) → ② 여권 기반 선불 유심으로 시작 → "
             "③ 외국인등록증 발급 후 본인 명의 번호로 전환 → ④ 등록증·서류로 은행 계좌 개설(여권, 등록증, 주소, 목적 확인서류).",
     "source": S_REGTIME,
     "completeness_checklist": ["외국인등록(90일 이내)", "선불 유심(여권)", "등록증 후 본인명의 전환", "계좌 개설"]},
]


def _enrich_calc(q):
    q = dict(q)
    q["grounding_evaluable"] = True
    q["latency_type"] = "calculation"
    q["cache_cluster"] = None
    q["multi_claim"] = True
    q.setdefault("completeness_checklist", None)
    q["metrics"] = ["grounding", "citation", "completeness", "latency"]
    return q


# ── ③ 최신성 버전쌍 — 구버전 vs 신버전을 섞어 A/B, 최신 우선 기대 ──
#    (보강방향.md의 버전·날짜 정보에 근거. 구버전의 '내용'은 원문에서 확인 필요)
FRESHNESS_PAIRS = [
    {"id": "fresh_1", "category": "insurance",
     "query": "유학생 건강보험 지역가입 적용 기준 최신으로 알려줘",
     "expected": "prefer_newest",
     "newest": {"label": "보건복지부고시 제2025-69호", "date": "2025-04-23", "source": S_NHISLAW},
     "older":  [{"label": "고시 제2024-290호", "date": "2024-12-30"},
                {"label": "고시 제2024-81호", "date": "2024-05-08"}],
     "note": "최신 고시(2025-69)를 우선 인용해야 정답. 구버전 인용 시 오답."},
    {"id": "fresh_2", "category": "visa",
     "query": "D-2 체류 서류 기준 최신 매뉴얼로 알려줘",
     "expected": "prefer_newest",
     "newest": {"label": "하이코리아 체류민원 매뉴얼", "date": "2026-06-01", "source": S_MANUAL},
     "older":  [{"label": "이전 수정이력본", "date": "2026-06-01 이전"}],
     "note": "체류 매뉴얼은 수시 수정. 최신 첨부본 기준."},
    {"id": "fresh_3", "category": "visa",
     "query": "사증(비자) 발급 서류 기준 최신으로 알려줘",
     "expected": "prefer_newest",
     "newest": {"label": "하이코리아 사증민원 매뉴얼", "date": "2026-05-21", "source": S_MANUAL},
     "older":  [{"label": "이전 사증 매뉴얼본", "date": "2026-05-21 이전"}],
     "note": "사증 매뉴얼 최신본 우선."},
    {"id": "fresh_4", "category": "bank",
     "query": "외국인등록증으로 은행 업무 어떻게 보는지 최신 기준 알려줘",
     "expected": "prefer_newest",
     "newest": {"label": "모바일 외국인등록증 금융업무 허용(금융위 보도자료)", "date": "2025-03-21 시행", "source": S_BANKNEWS},
     "older":  [{"label": "출입국관리법 개정 시행", "date": "2023-12-14"}],
     "note": "2025-03 모바일 등록증 금융업무 허용을 우선 반영해야 정답."},
    {"id": "fresh_5", "category": "support",
     "query": "부산 외국인 지원기관 정보 최신으로 알려줘",
     "expected": "prefer_newest",
     "newest": {"label": "부산시 외국인주민지원 페이지", "date": "2026-03-30 업데이트", "source": S_BUSANSUP},
     "older":  [{"label": "부산외국인근로자지원센터 개소 등 이전 안내", "date": "2024-05-22"}],
     "note": "최신 업데이트 페이지 우선."},
    {"id": "fresh_6", "category": "academic",
     "query": "이번 학년도 수강신청·등록 안내 최신으로 알려줘",
     "expected": "prefer_newest",
     "newest": {"label": "2026학년도 1학기 수강신청/등록 안내", "date": "2026", "source": S_ENROLL},
     "older":  [{"label": "직전 학기 공지(교체형)", "date": "이전 학기"}],
     "note": "학기 교체형 공지 → 최신 학기 공지 우선(크롤러 연계)."},
]

# ── 최종 데이터셋 ──
EVAL = [_enrich(q) for q in _BASE] + [_enrich_calc(q) for q in _CALC]


if __name__ == "__main__":
    from collections import Counter
    print("총 문항:", len(EVAL), "(+ 최신성 쌍", len(FRESHNESS_PAIRS), ")")
    print("latency_type:", dict(Counter(q["latency_type"] for q in EVAL)))
    print("grounding 대상:", sum(q["grounding_evaluable"] for q in EVAL))
    print("citation 대상(multi_claim):", sum(q["multi_claim"] for q in EVAL))
    print("completeness 대상:", sum(1 for q in EVAL if q["completeness_checklist"]))
    print("cache 클러스터 수:", len(_CACHE_CLUSTERS),
          "/ 클러스터 소속 문항:", sum(1 for q in EVAL if q["cache_cluster"]))
    print()
    print("지표별 측정 가능 문항 수:")
    allm = Counter(m for q in EVAL for m in q["metrics"])
    allm["freshness"] = len(FRESHNESS_PAIRS)
    for k in ["grounding", "citation", "freshness", "latency", "cache", "completeness"]:
        print(f"  {k:13s}: {allm[k]}")
