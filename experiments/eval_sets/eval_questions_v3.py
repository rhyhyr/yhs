"""
YHS 평가 질문셋 v3 — 100문항

변경 내용 (v2→v3):
  - in_db 38개 제거 (단일 문서 fast-path 질문)
  - cross_hop 58개 신규 추가 (반드시 2개 이상 source_file 조합 필요)
  - complex 26 / uncovered 12 / dirty 4 유지
  총계: cross_hop 58 + complex 26 + uncovered 12 + dirty 4 = 100

변경 내용 (v3 → v3.1, 크롤러 실측 대응):
  - cross_hop 58 → 50 (근접 중복 문항 8개 제거, 클러스터별 다양성은 유지)
  - uncovered 12 → 20 (8개 신규 추가, 크롤러 실제 호출 검증 목적)
  총계: cross_hop 50 + complex 26 + uncovered 20 + dirty 4 = 100

cross_hop 설계 원칙:
  - 단일 문서 청크만으로는 완전한 답변 불가
  - 서로 다른 source_file 2개 이상의 내용을 종합해야 정답
  - gold는 DB 청크 실제 내용 기반 (chunk_contents.txt 검증 완료)
"""

from experiments.eval_sets.eval_questions_v2 import (
    EVAL_QUERIES as _BASE_QUERIES,
)
from experiments.eval_sets.eval_questions_v2 import (
    S_ACTOUT,
    S_BANKNEWS,
    S_CHGSTATUS,
    S_DONGAINS,
    S_DONGAINTL,
    S_DONGAVISA,
    S_GLOBALHS,
    S_HANLIM,
    S_IMM1345,
    S_IMMARREAR,
    S_KOTRATEL,
    S_LOA,
    S_MOBILEID,
    S_NHISLAW,
    S_REGCHG,
    S_REGTIME,
    S_REISSUE,
    S_RETURN,
    S_SCH_EN_UG,
    S_SCH_KR_UG,
    S_STUDYKR,
    S_TUITION,
)

S_INSURANCE_ARREARS = S_IMMARREAR
S_EXT_PERMIT        = S_STUDYKR
S_MOBILE_BANK       = S_BANKNEWS
S_MOBILE_ID_ISSUE   = S_MOBILEID
S_DORM              = S_DONGAINTL
S_TELECOM           = S_KOTRATEL
S_CHGADDR           = S_REGCHG
S_LOA_DONGA         = S_LOA
S_RETURN_DONGA      = S_RETURN
S_TUITION_2026      = S_TUITION
S_SCH_KR            = S_SCH_KR_UG
S_SCH_EN            = S_SCH_EN_UG
S_NHIS_BASE         = S_NHISLAW

_KEEP_STRATA = {"complex", "uncovered", "dirty"}

# uncovered 12 → 20 확장분 (8개). 크롤러 실제 발화 검증 목적으로 추가.
# 주의: gold는 기존 12개와 동일하게 "[크롤러] ... 확인 필요" 형식만 채움 (구체적 날짜/사실은
# 정적으로 알 수 없으므로 의도적으로 비워둠 — 판정 루브릭상 "최신 확인 안내"가 정답).
# source 중 "TODO 확인 필요"로 표시된 항목은 allowed_sites 도메인 내에 실제 게시판 URL이
# 존재하는지 실행 전에 직접 확인 필요함 (확인 안 된 URL을 그대로 두면 크롤러가 빈 결과를 반환함).
_UNCOVERED_EXTRA = [
    {"id": "ac_uncov_3", "lang": "ko", "category": "academic", "stratum": "uncovered",
     "query": "이번 학기 졸업사정(졸업요건 심사) 신청 마감일 언제야?",
     "expected_intent": "academic",
     "gold": "[크롤러] 학기별 졸업사정 신청 공지(교체형) → 동아대 학사 안내 최신 페이지 확인 필요.",
     "source": "TODO 확인 필요 (donga.ac.kr 학사공지 게시판 — 정확한 mCode 미확인)"},

    {"id": "r_uncov_1", "lang": "ko", "category": "academic", "stratum": "uncovered",
     "query": "다음 학기 복학 신청 기간 언제부터야?",
     "expected_intent": "academic",
     "gold": "[크롤러] 학기별 복학 신청 기간(교체형) → 동아대 학사 안내 최신 페이지 확인 필요.",
     "source": "TODO 확인 필요 (donga.ac.kr 학사공지 게시판 — 정확한 mCode 미확인)"},

    {"id": "w_uncov_2", "lang": "ko", "category": "work", "stratum": "uncovered",
     "query": "이번 학기 시간제취업 허가 연장(재신청) 마감일 언제야?",
     "expected_intent": "work",
     "gold": "[크롤러] 학기별 공지 → 동아대 국제교류과 시간제취업 안내 확인 필요.",
     "source": "https://rfc.donga.ac.kr/global/CMS/Contents/Contents.do?mCode=MN064"},

    {"id": "im_uncov_1", "lang": "ko", "category": "visa", "stratum": "uncovered",
     "query": "이번 달 하이코리아 통합신청서비스 시스템 점검 일정 있어?",
     "expected_intent": "visa",
     "gold": "[크롤러] 시스템 점검은 비정기 공지이므로 → 하이코리아 공지사항 최신 페이지 확인 필요.",
     "source": "TODO 확인 필요 (hikorea.go.kr 공지사항 — 정확한 게시판 경로 미확인)"},

    {"id": "im_uncov_2", "lang": "ko", "category": "visa", "stratum": "uncovered",
     "query": "부산출입국·외국인청 이번 주 민원 상담 운영시간 변동 있어?",
     "expected_intent": "visa",
     "gold": "[크롤러] 운영시간 변동 공지 → 출입국·외국인청 안내 페이지에서 최신 확인 필요.",
     "source": S_IMM1345},

    {"id": "t_uncov_1", "lang": "ko", "category": "admin", "stratum": "uncovered",
     "query": "올해 외국인 유학생도 종합소득세 신고 대상이면 신고 기간이 언제까지야?",
     "expected_intent": "admin",
     "gold": "[크롤러] 연도별 종합소득세 신고기간 공지 → 홈택스 최신 공지 확인 필요.",
     "source": "TODO 확인 필요 (hometax.go.kr 공지사항 — 정확한 게시판 경로 미확인)"},

    {"id": "h_uncov_3", "lang": "ko", "category": "housing", "stratum": "uncovered",
     "query": "석당 글로벌하우스 이번 학기 퇴사(퇴소) 신청 마감일 언제야?",
     "expected_intent": "housing",
     "gold": "[크롤러] 학기별 퇴사 신청 공지 → 석당 글로벌하우스 페이지 확인 필요.",
     "source": S_GLOBALHS},

    {"id": "s_uncov_2", "lang": "ko", "category": "scholarship", "stratum": "uncovered",
     "query": "다음 학기 성적우수 장학금 발표일 언제야?",
     "expected_intent": "scholarship",
     "gold": "[크롤러] 학기별 장학 발표 공지 → 국제교류과 장학 페이지 확인 필요.",
     "source": "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN112"},
]

assert len(_UNCOVERED_EXTRA) == 8, f"uncovered 추가분 8개 필요: 현재 {len(_UNCOVERED_EXTRA)}개"

_EXISTING = [q for q in _BASE_QUERIES if q["stratum"] in _KEEP_STRATA] + _UNCOVERED_EXTRA

_CROSS_HOP = [

    # ── [보험체납 → 비자 제한] 05번 + 20번 (3개) ─────────────────────────
    {"id": "ch_vi_1", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "건강보험료 미납이 있으면 D-2 비자 연장할 때 어떻게 돼?",
     "expected_intent": "health_insurance",
     "gold": "체납 확인제도에 따라 비자 연장 신청 시 체납 여부를 확인한다. "
             "미납 시 원칙적으로 6개월 이하로만 체류연장이 허가되며, "
             "체납액을 모두 납부하면 정상 연장(통상 2~5년)이 가능하다.",
     "source": f"{S_INSURANCE_ARREARS} / {S_DONGAINS}"},

    {"id": "ch_vi_2", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "보험료 체납 있어도 전부 납부하면 비자 정상 연장돼?",
     "expected_intent": "health_insurance",
     "gold": "네, 체납액을 모두 납부하면 정상적으로 비자연장이 가능하다(통상 2~5년). "
             "미납 상태에서 신청하면 원칙적으로 6개월 이하만 허가되므로, "
             "연장 신청 전에 건강보험료와 세금 체납 여부를 확인해야 한다.",
     "source": f"{S_INSURANCE_ARREARS} / {S_DONGAINS}"},

    {"id": "ch_vi_3", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "비자 연장 전에 세금이랑 건강보험료 둘 다 확인받아?",
     "expected_intent": "health_insurance",
     "gold": "네, 체납 확인제도에서 세금과 건강보험료 체납 여부를 모두 확인한다. "
             "관계부처 간 체납정보가 공유되며 출입국 담당자가 비자 연장 신청 시 이를 확인한다.",
     "source": f"{S_INSURANCE_ARREARS} / {S_DONGAINS}"},

    # ── [외국인등록 → 통신] 01번 + 09번 (2개) ───────────────────────────
    {"id": "ch_vt_1", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "외국인등록증 받으면 바로 후불 핸드폰 개통할 수 있어?",
     "expected_intent": "telecom",
     "gold": "후불휴대전화 개통 시 외국인등록증 또는 국내 거소신고증 지참이 필수이다. "
             "외국인등록증 수령 후 개통 가능하며, 본인 명의 통장 또는 신용카드로만 납부 가능하다. "
             "체류코드에 따라 개통 대수·할부 여부 등 세부사항이 달라진다.",
     "source": f"{S_REGTIME} / {S_TELECOM}"},

    {"id": "ch_vt_2", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "외국인등록 하기 전에도 후불 핸드폰 개통 가능해?",
     "expected_intent": "telecom",
     "gold": "후불휴대전화 개통에는 외국인등록증 또는 거소신고증이 필수이므로, "
             "외국인등록 전에는 후불 개통이 불가하다.",
     "source": f"{S_REGTIME} / {S_TELECOM}"},

    # ── [외국인등록 → 은행] 01번 + 32번 (2개) ───────────────────────────
    {"id": "ch_vb_1", "lang": "ko", "category": "bank", "stratum": "cross_hop",
     "query": "외국인등록하면 바로 은행 계좌 개설 가능해?",
     "expected_intent": "banking",
     "gold": "외국인등록증 발급 후 은행 계좌 개설이 가능하다. "
             "2025년 3월 21일부터는 모바일 외국인등록증으로도 "
             "신한·하나·아이엠뱅크·부산·전북·제주 등 6개 은행에서 대면 계좌개설이 가능하다.",
     "source": f"{S_REGTIME} / {S_MOBILE_BANK}"},

    {"id": "ch_vb_2", "lang": "ko", "category": "bank", "stratum": "cross_hop",
     "query": "모바일 외국인등록증으로 통장 개설되는 은행이 어디야?",
     "expected_intent": "banking",
     "gold": "2025년 3월 21일부터 가능하다. "
             "대면 업무처리 가능 은행: 신한, 하나, 아이엠뱅크, 부산, 전북, 제주(6개). "
             "비대면 업무처리 가능 은행: 전북은행(1개).",
     "source": S_MOBILE_BANK},

    # ── [모바일등록증 발급 조건] 33번 + 01번 (3개) ──────────────────────
    {"id": "ch_mob_1", "lang": "ko", "category": "bank", "stratum": "cross_hop",
     "query": "모바일 외국인등록증 만들려면 뭐가 필요해?",
     "expected_intent": "mobile_id",
     "gold": "IC 칩이 내장된 외국인등록증이 먼저 필요하다. "
             "IC 외국인등록증 발급 준비물: 6개월 이내 사진(3.5×4.5cm), 여권, 체류지 입증 서류, 수수료 3만 5천원. "
             "이후 '대한민국 모바일 신분증' 앱에서 스마트폰에 IC 등록증을 태그하여 발급.",
     "source": f"{S_MOBILE_ID_ISSUE} / {S_REGTIME}"},

    {"id": "ch_mob_2", "lang": "ko", "category": "bank", "stratum": "cross_hop",
     "query": "외국인등록 하자마자 모바일 등록증 바로 만들 수 있어?",
     "expected_intent": "mobile_id",
     "gold": "외국인등록 후 IC 칩 내장 외국인등록증을 발급받아야 모바일 등록증 발급이 가능하다. "
             "IC 등록증 소지자는 스마트폰 태그 후 본인인증으로 즉시 발급 가능하다.",
     "source": f"{S_REGTIME} / {S_MOBILE_ID_ISSUE}"},

    {"id": "ch_mob_3", "lang": "ko", "category": "bank", "stratum": "cross_hop",
     "query": "IC 칩 없는 기존 외국인등록증으로 모바일 등록증 발급 가능해?",
     "expected_intent": "mobile_id",
     "gold": "기존 외국인등록증(IC 칩 없는 것) 소지자는 출입국·외국인 관서를 방문하여 QR코드로 발급받아야 한다. "
             "스마트폰 태그 방식은 IC 칩 내장 등록증에서만 가능하다.",
     "source": f"{S_MOBILE_ID_ISSUE} / {S_REISSUE}"},

    # ── [체류자격변경 → 외국인등록] 06번 + 01번 (3개) ──────────────────
    {"id": "ch_vc_1", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "D-4에서 D-2로 자격 바꾸면 외국인등록도 다시 해야 해?",
     "expected_intent": "visa",
     "gold": "체류자격변경허가를 받은 외국인은 그 허가를 받는 즉시 외국인등록을 해야 한다. "
             "외국인등록증에는 변경된 허가사항이 기재되어 갱신된다.",
     "source": f"{S_CHGSTATUS} / {S_REGTIME}"},

    {"id": "ch_vc_2", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "어학연수 끝나고 대학 입학하면 비자 변경 절차가 어떻게 돼?",
     "expected_intent": "visa",
     "gold": "D-4 어학연수 후 D-2 유학으로 변경 시 새 활동(유학) 시작 전에 관할 출입국관리사무소에서 "
             "체류자격변경허가를 받아야 한다. "
             "서류: 체류자격변경허가 신청서, 여권, 외국인등록증, 체류자격별 첨부서류, 수수료. "
             "허가 후 외국인등록증에 허가사항이 기재된다.",
     "source": f"{S_CHGSTATUS} / {S_DONGAVISA}"},

    {"id": "ch_vc_3", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "체류자격 변경하면 외국인등록증을 새로 발급받아야 해?",
     "expected_intent": "visa",
     "gold": "새 발급이 아닌 기재 업데이트 방식이다. "
             "체류자격변경 허가 시 여권에 변경허가인이 날인되고, 외국인등록증에 허가사항이 기재된다.",
     "source": f"{S_CHGSTATUS} / {S_REISSUE}"},

    # ── [체류자격변경 → 보험] 06번 + 20번 (2개) ────────────────────────
    {"id": "ch_vci_1", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "D-4에서 D-2로 비자 바꾸면 건강보험도 새로 가입해야 해?",
     "expected_intent": "health_insurance",
     "gold": "D-2와 D-4 모두 건강보험 당연가입 대상이므로 별도 신청 없이 공단에서 일괄 처리된다. "
             "체류자격이 변경되어도 당연가입 상태는 유지되며, 거소지 변경 시 주소 신고만 하면 된다.",
     "source": f"{S_CHGSTATUS} / {S_DONGAINS}"},

    {"id": "ch_vci_2", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "어학연수에서 학부로 올라가면 보험료가 달라져?",
     "expected_intent": "health_insurance",
     "gold": "D-4→D-2 자격변경 자체로 보험료 기준이 달라지지는 않는다. "
             "지역가입자 보험료는 소득·재산 기준으로 산정되며, 산정액이 전년도 평균보험료보다 낮으면 "
             "평균보험료(71,920원, 2023년 기준)를 부과한다.",
     "source": f"{S_DONGAINS} / {S_NHIS_BASE}"},

    # ── [시간제취업 → 비자] 02번 + 07번 (3개) ───────────────────────────
    {"id": "ch_wv_1", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "D-4 비자로 아르바이트 허가받으려면 언제부터 가능해?",
     "expected_intent": "work",
     "gold": "D-4(일반연수) 비자 소지자는 외국인등록 후 6개월이 경과한 이후부터 시간제취업 허가 신청이 가능하다.",
     "source": f"{S_ACTOUT} / {S_DONGAVISA}"},

    {"id": "ch_wv_2", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "아르바이트 허가 없이 일하다 걸리면 어떻게 돼?",
     "expected_intent": "work",
     "gold": "체류자격외활동허가 없이 취업하다 적발되면 벌금 부과 및 강제출국 처벌을 받을 수 있다.",
     "source": f"{S_ACTOUT} / {S_DONGAVISA}"},

    {"id": "ch_wv_4", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "시간제취업 허가 받으면 비자 연장 서류가 달라져?",
     "expected_intent": "work",
     "gold": "시간제취업 허가 자체가 비자 연장 기본 서류에 추가되지는 않는다. "
             "단, 허가 유지 조건(직전학기 출석률 90% 이상, 평점 2.0 이상)이 비자 연장 조건과 일부 겹친다.",
     "source": f"{S_DONGAVISA} / {S_ACTOUT}"},

    # ── [시간제취업 → 보험] 02번 + 20번 (2개) ──────────────────────────
    {"id": "ch_wi_1", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "아르바이트 시작하면 건강보험이 어떻게 바뀌어?",
     "expected_intent": "health_insurance",
     "gold": "D-2/D-4 유학생은 이미 지역가입자로 당연가입되어 있다. "
             "시간제취업(아르바이트)을 해도 직장가입자로 자동 전환되지 않으며, 지역가입 상태가 유지된다. "
             "월 보험료(71,920원, 2023년 기준)는 계속 납부해야 한다.",
     "source": f"{S_ACTOUT} / {S_DONGAINS}"},

    {"id": "ch_wi_2", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "아르바이트 수입이 생기면 보험료가 올라가?",
     "expected_intent": "health_insurance",
     "gold": "지역가입자 보험료는 소득·재산 등을 기준으로 산정된다. "
             "단, 산정된 보험료가 전년도 11월말 전체 평균보험료보다 낮으면 평균보험료를 부과한다. "
             "아르바이트 소득 변화로 보험료가 조정될 수 있으나 구체적 변화는 국민건강보험공단에 확인 필요.",
     "source": f"{S_NHIS_BASE} / {S_DONGAINS}"},

    # ── [기숙사 → 체류지변경] 08번 + 11번 (2개) ─────────────────────────
    {"id": "ch_hr_1", "lang": "ko", "category": "housing", "stratum": "cross_hop",
     "query": "기숙사 들어가면 체류지 변경신고 해야 해?",
     "expected_intent": "housing",
     "gold": "네, 체류지(주소)가 변경되면 변경일로부터 14일 이내(동아대 국제교류과 기준) 또는 "
             "15일 이내(하이코리아 기준)에 출입국관리사무소에 신고해야 한다. "
             "미신고 시 출입국관리법 위반으로 과태료가 부과된다.",
     "source": f"{S_DONGAVISA} / {S_CHGADDR}"},

    {"id": "ch_hr_2", "lang": "ko", "category": "housing", "stratum": "cross_hop",
     "query": "기숙사에서 나와서 자취방으로 이사하면 어디에 신고해?",
     "expected_intent": "housing",
     "gold": "체류지 변경 시 변경일로부터 14~15일 이내에 관할 지방출입국·외국인관서에 신고해야 한다. "
             "준비물: 통합신청서, 여권, 외국인등록증, 임대차계약서 등 변경 입증 서류.",
     "source": f"{S_DONGAVISA} / {S_CHGADDR}"},

    # ── [기숙사 → 비자서류] 08번 + 07번 (2개) ──────────────────────────
    {"id": "ch_hv_1", "lang": "ko", "category": "housing", "stratum": "cross_hop",
     "query": "기숙사 살면 비자 연장할 때 체류지 증명은 어떻게 해?",
     "expected_intent": "housing",
     "gold": "기숙사 거주자는 '거주숙소제공사실확인서'를 학교(국제교류과)에서 수령하여 제출하면 된다. "
             "본인 명의 집이 아닌 경우와 달리 임대차계약서 대신 학교 발행 확인서로 대체 가능하다.",
     "source": f"{S_DONGAVISA} / {S_DORM}"},

    {"id": "ch_hv_2", "lang": "ko", "category": "housing", "stratum": "cross_hop",
     "query": "한림생활관에 살면 비자 연장 체류지 서류를 학교에서 받아?",
     "expected_intent": "housing",
     "gold": "네, 기숙사 거주자는 비자(체류기간) 연장 시 '거주숙소제공사실확인서'를 학교에서 수령하여 제출한다. "
             "한림생활관은 승학캠퍼스 내에 있으며, 해당 캠퍼스 국제교류과에서 발급받을 수 있다.",
     "source": f"{S_DONGAVISA} / {S_HANLIM}"},

    # ── [휴학 → 비자] 22번 + 07번 + 12번 (3개) ─────────────────────────
    {"id": "ch_lv_1", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "유학생이 휴학하면 D-2 비자에 어떤 영향이 있어?",
     "expected_intent": "visa",
     "gold": "유학생의 휴학은 체류자격 유지에 영향을 줄 수 있다. "
             "반드시 국제교류과와 출입국사무소에 먼저 확인한 후 휴학 신청을 해야 한다.",
     "source": f"{S_LOA_DONGA} / {S_DONGAVISA}"},

    {"id": "ch_lv_2", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "휴학하기 전에 출입국에 신고해야 해?",
     "expected_intent": "visa",
     "gold": "의무 사전 신고 규정은 별도로 없으나, 동아대 안내에 따르면 "
             "유학생은 휴학 전에 반드시 국제교류과와 출입국에 먼저 확인하도록 안내하고 있다.",
     "source": f"{S_LOA_DONGA} / {S_DONGAVISA}"},

    {"id": "ch_lv_3", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "휴학 기간 중에 비자가 만료되면 어떻게 해?",
     "expected_intent": "visa",
     "gold": "휴학 중이라도 체류기간 만료 전에 별도로 비자 연장 신청을 해야 한다. "
             "체류기간연장허가는 만료일 4개월 전부터 근무일 기준 1일 전까지 신청 가능하다. "
             "유학생은 휴학이 체류자격에 영향을 줄 수 있으므로 국제교류과와 출입국에 미리 확인해야 한다.",
     "source": f"{S_LOA_DONGA} / {S_EXT_PERMIT}"},

    # ── [휴학 → 보험] 22번 + 20번 + 05번 (2개) ─────────────────────────
    {"id": "ch_li_1", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "휴학하면 건강보험 계속 내야 해?",
     "expected_intent": "health_insurance",
     "gold": "6개월 이상 체류 외국인은 휴학과 무관하게 지역가입자로 당연가입 상태가 유지된다. "
             "따라서 휴학 중에도 월 보험료(71,920원, 2023년 기준)는 계속 납부해야 한다.",
     "source": f"{S_LOA_DONGA} / {S_DONGAINS}"},

    {"id": "ch_li_2", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "휴학 중 보험료 안 내면 복학 후 비자 연장에 문제 생겨?",
     "expected_intent": "health_insurance",
     "gold": "네, 보험료 미납(체납) 시 비자연장 등 체류허가 신청 시 불이익이 생긴다. "
             "복학 후 비자 연장 시 체납이 있으면 원칙적으로 6개월 이하로만 연장이 허가된다.",
     "source": f"{S_INSURANCE_ARREARS} / {S_DONGAINS}"},

    # ── [복학 → 등록금] 23번 + 25번 (2개) ──────────────────────────────
    {"id": "ch_ra_1", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "복학하면 등록금 납부는 어떻게 해?",
     "expected_intent": "academic",
     "gold": "복학생은 학적상태가 '복학'에서 '재학'으로 변경된 후 등록금 고지서 출력이 가능하다. "
             "수납처는 재학생과 동일하며 부산은행, 농협은행(지역농협 포함) 전국 지점 가상계좌를 이용한다. "
             "등록기간 중 복학한 학생은 차기 등록기간에 납부해야 한다.",
     "source": f"{S_RETURN_DONGA} / {S_TUITION_2026}"},

    {"id": "ch_ra_2", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "복학 신청하고 등록금 납부까지 순서가 어떻게 돼?",
     "expected_intent": "academic",
     "gold": "① 인터넷으로 복학 신청 → ② 학적상태 '복학'→'재학' 변경 확인 → "
             "③ 동아대 통합정보시스템에서 등록금 고지서 출력 → "
             "④ 부산은행/농협은행 가상계좌로 납부(또는 BC카드).",
     "source": f"{S_RETURN_DONGA} / {S_TUITION_2026}"},

    # ── [복학 → 비자] 23번 + 07번 (2개) ────────────────────────────────
    {"id": "ch_rv_1", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "휴학 후 복학할 때 비자도 갱신해야 해?",
     "expected_intent": "visa",
     "gold": "복학 자체가 비자 자동 갱신으로 이어지지는 않는다. "
             "체류기간 만료 전에 별도로 비자 연장 신청이 필요하며, "
             "복학 후 재학증명서 등 서류를 갖춰 신청하면 된다.",
     "source": f"{S_RETURN_DONGA} / {S_DONGAVISA}"},

    {"id": "ch_rv_2", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "복학하면 재학증명서로 비자 연장 서류에 쓸 수 있어?",
     "expected_intent": "visa",
     "gold": "네, 복학 후 재학생 신분이 되면 재학증명서를 발급받아 비자 연장 서류로 사용할 수 있다. "
             "비자 연장 기본 서류에 재학증명서가 포함된다.",
     "source": f"{S_RETURN_DONGA} / {S_DONGAVISA}"},

    # ── [장학금 → 비자] 26/27번 + 07번 (3개) ───────────────────────────
    {"id": "ch_sv_1", "lang": "ko", "category": "scholarship", "stratum": "cross_hop",
     "query": "장학금 받으면 비자 연장 때 재정능력 증빙 안 해도 돼?",
     "expected_intent": "scholarship",
     "gold": "성적 2.0 이상 재학생은 비자 연장 시 재정능력 증빙(은행잔고증명)이 기본 서류에 포함되지 않는다. "
             "장학금 수령이 재정능력 증빙을 공식 대체하는지는 DB에 명시되지 않으므로 국제교류과에 확인이 필요하다.",
     "source": f"{S_DONGAVISA} / {S_SCH_KR}"},

    {"id": "ch_sv_2", "lang": "ko", "category": "scholarship", "stratum": "cross_hop",
     "query": "장학금 유지 조건인 성적 기준이 비자 연장 성적 기준과 같아?",
     "expected_intent": "scholarship",
     "gold": "다르다. 비자 연장은 성적 2.0(C학점) 기준이다. "
             "한국어트랙 재학 장학금은 상위 60%/80% 등 상대적 순위 기준이고, "
             "영어트랙 재학 장학금은 상위 5%/20%/40%/100%로 구분된다.",
     "source": f"{S_DONGAVISA} / {S_SCH_KR} / {S_SCH_EN}"},

    {"id": "ch_sv_3", "lang": "ko", "category": "scholarship", "stratum": "cross_hop",
     "query": "장학금 못 받으면 비자 연장이 어려워지나?",
     "expected_intent": "scholarship",
     "gold": "장학금 수령 여부가 비자 연장에 직접 영향을 주지는 않는다. "
             "비자 연장의 핵심 조건은 성적 2.0 이상, 재학 중, 출석률 등이다. "
             "성적 2.0 미만이면 은행잔고증명(1600만원) 서류가 추가된다.",
     "source": f"{S_DONGAVISA} / {S_SCH_KR}"},

    # ── [장학금 → 등록금] 26/27번 + 25번 (1개) ─────────────────────────
    {"id": "ch_sa_1", "lang": "ko", "category": "scholarship", "stratum": "cross_hop",
     "query": "장학금으로 등록금을 전액 낼 수 있어?",
     "expected_intent": "scholarship",
     "gold": "한국어트랙 A등급(TOPIK 5급 이상)과 영어트랙 A등급(IELTS 7.0 / TOEFL iBT 90 / New TEPS 428 이상)은 "
             "첫 학기 등록금 전액 장학금이다. "
             "재학생 장학금도 성적에 따라 20~100% 지원된다.",
     "source": f"{S_SCH_KR} / {S_SCH_EN} / {S_TUITION_2026}"},

    # ── [등록금 → 비자] 25번 + 07번 (1개) ─────────────────────────────
    {"id": "ch_av_1", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "등록금 납부 증명서가 비자 연장에 필요해?",
     "expected_intent": "visa",
     "gold": "D-4→D-2 체류자격 변경 시 등록금납입증명서 제출이 필요하다. "
             "일반 D-2 비자 연장(재학생)에는 기본 서류에 명시되지 않으나, "
             "수료자·초과학기 연장 시에는 등록금납입증명서가 필요하다.",
     "source": f"{S_DONGAVISA} / {S_TUITION_2026}"},

    # ── [체류지변경 → 보험] 11번 + 20번 (2개) ──────────────────────────
    {"id": "ch_ri_1", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "이사하면 건강보험 주소도 바꿔야 해?",
     "expected_intent": "health_insurance",
     "gold": "네, 건강보험 지역가입자는 거소지 변경 시 정확한 주소 신고가 필요하다. "
             "출입국 체류지 변경신고(14~15일 이내)와 함께 건강보험 주소도 국민건강보험공단에 갱신해야 한다.",
     "source": f"{S_CHGADDR} / {S_DONGAINS}"},

    {"id": "ch_ri_2", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "체류지 변경 신고 안 하면 보험료 고지서가 이전 주소로 나와?",
     "expected_intent": "health_insurance",
     "gold": "거소지 변경 신고를 하지 않으면 출입국관리법 제35조 위반으로 과태료가 부과된다. "
             "건강보험 주소도 구 주소로 처리되어 보험료 고지서가 이전 주소로 발송될 수 있다.",
     "source": f"{S_CHGADDR} / {S_DONGAINS}"},

    # ── [비자연장+기숙사 서류] 07번 + 08번 (1개) ─────────────────────
    {"id": "ch_vh_1", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "기숙사 사는 외국인 비자 연장할 때 체류지 증명 서류 뭐야?",
     "expected_intent": "visa",
     "gold": "기숙사 거주자는 '거주숙소제공사실확인서'를 학교(국제교류과)에서 수령하여 제출한다. "
             "본인 명의 주택=임대차계약서 사본, 타인 명의=계약서+거주확인서+신분증 사본. "
             "기숙사는 학교 발행 확인서로 처리한다.",
     "source": f"{S_DONGAVISA} / {S_DORM}"},

    # ── [취업+자격변경] 02번 + 06번 (1개) ──────────────────────────────
    {"id": "ch_wvc_1", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "아르바이트 허가 받고 있는 D-4인데 D-2로 바꾸면 허가는 어떻게 돼?",
     "expected_intent": "work",
     "gold": "D-4→D-2 체류자격변경 후에는 D-2 기준으로 시간제취업 허가를 재신청해야 한다. "
             "체류자격변경허가는 새 활동 시작 전 관할 출입국관리사무소에서 받아야 하며, "
             "변경 후 D-2 기준 취업허가를 새로 받으면 된다.",
     "source": f"{S_ACTOUT} / {S_CHGSTATUS}"},

    # ── [외국인등록 → 비자연장 흐름] 01번 + 12번 (1개) ─────────────────
    {"id": "ch_vreg_1", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "처음 외국인등록 하고 비자 연장은 언제 신청하면 돼?",
     "expected_intent": "visa",
     "gold": "외국인등록은 입국 후 90일 이내에 해야 한다. "
             "이후 체류기간 만료일 4개월 전부터 근무일 기준 1일 전까지 비자 연장 신청이 가능하다. "
             "수수료는 5만원이며 처리기간은 일반 10일, 조사 필요 시 2개월이다.",
     "source": f"{S_REGTIME} / {S_EXT_PERMIT}"},

    # ── [취업+체류지변경] 07번 + 11번 (1개) ─────────────────────────────
    {"id": "ch_wreg_1", "lang": "ko", "category": "work", "stratum": "cross_hop",
     "query": "아르바이트 하는 곳이랑 내가 사는 곳이 다른데 신고해야 해?",
     "expected_intent": "visa",
     "gold": "체류지 신고는 실제 거주지를 기준으로 한다. "
             "아르바이트(직장) 주소가 아닌 거주지 주소가 변경될 때만 체류지 변경신고(14~15일 이내)를 해야 한다.",
     "source": f"{S_DONGAVISA} / {S_CHGADDR}"},

    # ── [외국인등록증 재발급+이사] 01번+10번 + 11번 (1개) ─────────────────
    {"id": "ch_reissue_1", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "외국인등록증 재발급받을 때 이사하면 주소도 같이 바꿀 수 있어?",
     "expected_intent": "arc",
     "gold": "외국인등록증 재발급(분실·훼손 등)과 체류지 변경 신고는 별개의 절차이다. "
             "이사 시 체류지 변경신고(변경일로부터 14~15일 이내)를 관할 출입국관리사무소에 별도 신청해야 한다.",
     "source": f"{S_REISSUE} / {S_CHGADDR}"},

    # ── [기숙사+보험 주소] 08번 + 20번 (1개) ────────────────────────────
    {"id": "ch_ih_1", "lang": "ko", "category": "insurance", "stratum": "cross_hop",
     "query": "기숙사 들어가면 건강보험 주소 신고 따로 해야 해?",
     "expected_intent": "health_insurance",
     "gold": "네, 기숙사 입사로 거소지가 변경되면 건강보험 주소도 갱신이 필요하다. "
             "체류지 변경신고(출입국)와 함께 국민건강보험공단에도 주소 변경 신고를 하는 것이 좋다.",
     "source": f"{S_DONGAINS} / {S_DORM}"},

    # ── [복학+비자+등록금 3-way] 23번 + 07번 + 25번 (1개) ───────────────
    {"id": "ch_rav_1", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "휴학하고 복학할 때 비자랑 등록금을 어떤 순서로 처리해야 해?",
     "expected_intent": "academic",
     "gold": "① 복학 신청(인터넷) → ② 학적상태 '복학'→'재학' 변경 확인 → "
             "③ 등록금 고지서 출력 및 납부(부산은행/농협은행 가상계좌) → "
             "④ 체류기간 만료 전 비자 연장 신청(만료 4개월 전부터 가능). "
             "유학생은 휴학이 체류자격에 영향을 줄 수 있으므로 복학 전 국제교류과와 출입국 확인 필요.",
     "source": f"{S_RETURN_DONGA} / {S_TUITION_2026} / {S_DONGAVISA}"},

    # ── [등록금 납부 후 휴학] 22번 + 25번 (1개) ─────────────────────────
    {"id": "ch_la_1", "lang": "ko", "category": "academic", "stratum": "cross_hop",
     "query": "등록금 납부하고 나서 휴학하면 등록금은 어떻게 돼?",
     "expected_intent": "academic",
     "gold": "등록 후 30일 이내 휴학 신청 시 전액 이월, 30~60일은 2/3 이월, "
             "60~90일은 1/2 이월, 90일 이후에는 이월 불가이다.",
     "source": f"{S_LOA_DONGA} / {S_TUITION_2026}"},

    # ── [모바일등록증+비대면계좌] 33번 + 32번 (1개) ────────────────────
    {"id": "ch_mb_1", "lang": "ko", "category": "bank", "stratum": "cross_hop",
     "query": "모바일 외국인등록증 발급받고 바로 비대면으로 통장 개설 가능해?",
     "expected_intent": "banking",
     "gold": "모바일 외국인등록증으로 비대면 업무처리가 가능한 은행은 전북은행 1곳이다. "
             "대면 업무처리 가능 은행은 신한, 하나, 아이엠뱅크, 부산, 전북, 제주 총 6곳이다. "
             "2025년 3월 21일부터 이용 가능하다.",
     "source": f"{S_MOBILE_ID_ISSUE} / {S_MOBILE_BANK}"},

    # ── [비자연장 수수료+처리기간] 12번 + 07번 (1개) ────────────────────
    {"id": "ch_vfee_1", "lang": "ko", "category": "visa", "stratum": "cross_hop",
     "query": "비자(체류기간) 연장 신청하면 수수료랑 처리기간이 어떻게 돼?",
     "expected_intent": "visa",
     "gold": "수수료: 하이코리아(전자민원) 기준 5만원, 동아대 국제교류과 안내 기준 6만원. "
             "처리기간: 일반사항 10일, 조사 필요 사항은 2개월까지 소요. "
             "체류기간 만료일 4개월 전부터 근무일 기준 1일 전까지 신청 가능하므로 여유 있게 신청 권장.",
     "source": f"{S_EXT_PERMIT} / {S_DONGAVISA}"},
]

assert len(_CROSS_HOP) == 50, f"cross_hop 50개 필요: 현재 {len(_CROSS_HOP)}개"

EVAL_QUERIES = _EXISTING + _CROSS_HOP

if __name__ == "__main__":
    from collections import Counter
    print(f"총 문항: {len(EVAL_QUERIES)}")
    cnt = Counter(q["stratum"] for q in EVAL_QUERIES)
    for s, n in sorted(cnt.items()):
        print(f"  {s}: {n}개")
