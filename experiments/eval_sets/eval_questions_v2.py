"""
YHS 기말 평가 질문셋 — 80문항 (gold 포함)

근거: 전 항목의 query·gold·source는 db_sources/ 수집 문서에서만 도출.
      gold는 Neo4j에 인덱싱된 청크 내용 기반.

필드: id, lang(ko/en/zh), category, stratum, query, expected_intent, gold, source
실제 분포: in_db 38 / complex 26 / uncovered 12 / dirty 4

⚠️ gold는 수집 시점(2026-06-10~17) 요약. 발표/운영 전 source 원문 재확인 권장.

v2 변경사항 (2026-06-19):
  - a_indb_1: 전화번호(DB 없음) → D-4→D-2 재정능력 입증금액
  - i_indb_3: 50% 할인(DB 없음) → 건강보험료 납부방법
  - i_cplx_2: 아르바이트→직장가입(19번 버그) → 보험료 월 금액
  - i_cplx_5: 직장가입자 조건(19번 버그) → 보험 비보장 항목
  - t_indb_1: 선불유심(09번 미수록) → 후불 체류코드별 차이
  - t_cplx_1: 선불 권장(09번 미수록) → 외국인등록증 없이 후불 개통 가능?
  - b_indb_3: 캠퍼스 근처 은행(DB 없음) → 모바일 외국인등록증 비대면 업무
  - t_dirty_1: gold에서 선불 정보 제거(선불 DB 미수록)
"""

S_MANUAL    = "https://www.hikorea.go.kr/board/BoardNtcDetailR.pt?BBS_GB_CD=BS10&BBS_SEQ=1&NTCCTT_SEQ=1062&page=1"
S_EXT       = "https://www.hikorea.go.kr/cvlappl/cvlapplInfoR.pt?CAT_SEQ=1808"
S_REGTIME   = "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=176&PARENT_ID=139"
S_REGDOCS   = "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=177&PARENT_ID=139"
S_REISSUE   = "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=178&PARENT_ID=139"
S_REGCHG    = "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=180&PARENT_ID=139"
S_CHGSTATUS = "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=184&PARENT_ID=141"
S_ACTOUT    = "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=187&PARENT_ID=142"
S_EMINWON   = "https://www.hikorea.go.kr/cvlappl/CvlapplStep1.pt"
S_VISAPORT  = "https://www.visa.go.kr/openPage.do?MENU_ID=10105"
S_DONGAVISA = "https://rfc.donga.ac.kr/global/CMS/Contents/Contents.do?mCode=MN064"
S_DONGAINTL = "https://rfc.donga.ac.kr/global/CMS/Contents/Contents.do?mCode=MN062"
S_NHISLAW   = "https://www.nhis.or.kr/lm/lmxsrv/law/lawFullContent.do?SEQ=41&SEQ_HISTORY=595302"
S_IMMARREAR = "https://www.immigration.go.kr/immigration/1522/subview.do"
S_DONGAINS  = "https://rfc.donga.ac.kr/global/CMS/Contents/Contents.do?mCode=MN063"
S_STUDYKR   = "https://www.studyinkorea.go.kr/in/life/residenceAndStayInfo.do?tab=stay-extension"
S_GOV24WORK = "https://foreigner.gov.kr/contents/foreignerContents/?htmlNo=m020103"
S_SCH_KR_UG = "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN112"
S_SCH_EN_UG = "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN077"
S_SCH_KR_GR = "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN109"
S_LOA       = "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN124"
S_RETURN    = "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN125"
S_ENROLL    = "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN316"
S_TUITION   = "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN318"
S_GLOBALHS  = "http://globalhouse.donga.ac.kr"
S_HANLIM    = "https://hanlim.donga.ac.kr"
S_BANKNEWS  = "https://www.fsc.go.kr/edu/news/84342"
S_MOBILEID  = "https://www.mobileid.go.kr/mip/hps/issuReqstGuidance/issuReqstGuidanceMfc.do"
S_KOTRATEL  = "https://ombudsman.kotra.or.kr/ik-kr/cntnts/i-217/web.do"
S_BUSANSUP  = "https://www.busan.go.kr/depart/family0407"
S_BUSANCALL = "https://bscfw.or.kr/notice_01.html"
S_IMM1345   = "https://www.immigration.go.kr/immigration/1530/subview.do"
S_BUSANIMM  = "https://www.immigration.go.kr/immigration/1678/subview.do"


EVAL_QUERIES = [
    # ── 비자·체류 (visa) 21 ──
    {"id": "v_indb_1", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "외국인등록은 입국 후 며칠 이내에 해야 해?", "expected_intent": "visa",
     "gold": "90일을 초과해 체류하려는 외국인은 입국일부터 90일 이내 등록. 체류자격 부여·변경을 받은 경우에는 즉시 등록.",
     "source": S_REGTIME},
    {"id": "v_indb_2", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "외국인등록 할 때 제출서류가 뭐야?", "expected_intent": "arc",
     "gold": "공통서류(통합신청서, 여권, 사진)에 D-2는 재학증명서, D-4는 연수기관 재학증명서 등. 동아대 실무로는 통합신청서·재학증명서·여권·비자 사본·사진·수수료.",
     "source": S_REGDOCS},
    {"id": "v_indb_3", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "외국인등록증을 잃어버리면 어떻게 재발급해?", "expected_intent": "arc",
     "gold": "분실·훼손·기재란 부족·인적사항 변경 시 재발급 대상. 하이코리아/관할 출입국에서 신청.",
     "source": S_REISSUE},
    {"id": "v_indb_4", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "D-4에서 D-2로 비자 바꾸려면 어떻게 해?", "expected_intent": "visa",
     "gold": "체류자격 변경허가 대상. 새 활동(유학) 시작 전에 관할 출입국관서에서 허가받아야 함.",
     "source": S_CHGSTATUS},
    {"id": "v_indb_5", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "D-4에서 D-2로 바꿀 때 필요한 서류는?", "expected_intent": "visa",
     "gold": "신청서, 사진, 여권 사본, 외국인등록증, 체류지 입증, 잔고증명, 학력입증서류, 어학연수 출석증명, 등록금 납부증명 등이 동아대 안내에 제시됨.",
     "source": S_DONGAVISA},
    {"id": "v_indb_6", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "체류기간 연장은 언제 신청해?", "expected_intent": "visa",
     "gold": "만료 전 신청. 하이코리아 전자민원에 D-2·D-4도 포함되나 개별 사안은 방문예약이 요구될 수 있음.",
     "source": S_EXT},
    {"id": "v_indb_7", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "체류기간 연장 신청 공통서류가 뭐야?", "expected_intent": "visa",
     "gold": "통합신청서, 여권, 외국인등록증, 체류지 입증서류, 수수료가 공통서류.",
     "source": S_EXT},
    {"id": "v_indb_8", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "이사했는데 체류지 변경 신고는 어디서 며칠 안에 해?", "expected_intent": "visa",
     "gold": "변경 사유 발생일부터 15일 이내 신고(미신고 시 과태료). 하이코리아 전자민원 또는 관할 출입국에서 처리.",
     "source": S_REGCHG},
    {"id": "v_indb_9", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "부산에서 체류 업무는 어디서 봐?", "expected_intent": "visa",
     "gold": "부산출입국·외국인청 종합민원센터(부산 중구 중앙대로 146, 051-461-3162). 체류·사증·국적·증명발급 취급.",
     "source": S_BUSANIMM},
    {"id": "v_indb_10", "lang": "ko", "category": "visa", "stratum": "in_db",
     "query": "D-2 체류기간 연장에 기본으로 내는 서류는?", "expected_intent": "visa",
     "gold": "통합신청서/사진, 외국인등록증, 여권 사본, 재학증명서, 성적증명서, 체류지 입증서류, 수수료.",
     "source": S_DONGAVISA},
    {"id": "v_cplx_1", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "성적이 2.0 미만인데 비자 연장 될까?", "expected_intent": "visa",
     "gold": "성적 2.0 미만·초과학기·졸업유예자는 은행잔고증명, 사유서, 지도교수 확인서 등이 추가될 수 있음. 최종은 출입국 판단.",
     "source": S_DONGAVISA},
    {"id": "v_cplx_2", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "학교 안내엔 체류지 변경 14일이라는데 법정 기준도 14일이야?", "expected_intent": "visa",
     "gold": "법정 기준은 변경일부터 15일 이내(하이코리아). 동아대 안내엔 14일 표기가 있어 14일 내 처리하면 안전하나 기준은 하이코리아/1345 우선.",
     "source": S_REGCHG},
    {"id": "v_cplx_3", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "휴학하면 D-2 체류자격에 영향 있어?", "expected_intent": "visa",
     "gold": "휴학·미등록·장기결석·초과학기·졸업유예 시 D-2 연장·자격 유지가 달라질 수 있음. 국제교류과와 출입국에 먼저 확인해야 함.",
     "source": S_DONGAINTL},
    {"id": "v_cplx_4", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "어학연수로 왔는데 출국 안 하고 국내에서 D-2로 바꿀 수 있어?", "expected_intent": "visa",
     "gold": "가능. 체류자격 변경허가로 새 활동 시작 전에 국내 관할 출입국관서에서 허가받으면 됨.",
     "source": S_CHGSTATUS},
    {"id": "v_cplx_5", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "사증발급인정서는 언제 필요해?", "expected_intent": "visa",
     "gold": "재외공관/비자포털 절차가 기본이며, 사증발급인정서가 필요한 경우 국내 초청자·기관 관할 출입국관서 절차가 추가됨.",
     "source": S_VISAPORT},
    {"id": "v_cplx_6", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "외국인등록 정보(여권·학교 등)가 바뀌면 어떻게 해?", "expected_intent": "arc",
     "gold": "성명·국적·여권·소속학교 변경 등은 15일 이내 변경신고. 미신고 시 과태료.",
     "source": S_REGCHG},
    {"id": "v_cplx_7", "lang": "ko", "category": "visa", "stratum": "complex",
     "query": "건강보험료 체납이 비자 연장에 영향을 줘?", "expected_intent": "visa",
     "gold": "연장 신청 시 건강보험 체납을 확인하며, 미납이 확인되면 원칙적으로 6개월 이하로 제한 연장될 수 있음.",
     "source": S_IMMARREAR},
    {"id": "v_uncov_1", "lang": "ko", "category": "visa", "stratum": "uncovered",
     "query": "이번 학기 체류기간 연장 방문예약 언제까지 받아?", "expected_intent": "visa",
     "gold": "[크롤러] 방문예약 가능일은 시기별로 변동 → 하이코리아 전자민원/방문예약 최신 페이지 확인 필요.",
     "source": S_EMINWON},
    {"id": "v_uncov_2", "lang": "ko", "category": "visa", "stratum": "uncovered",
     "query": "이번 학기 외국인등록 학교 단체 신청 일정 알려줘", "expected_intent": "visa",
     "gold": "[크롤러] 학기별 공지 사항 → 동아대 국제교류과 안내 페이지 확인 필요.",
     "source": S_DONGAINTL},
    {"id": "v_uncov_3", "lang": "ko", "category": "visa", "stratum": "uncovered",
     "query": "부산출입국 이번 달 방문예약 빈자리 있어?", "expected_intent": "visa",
     "gold": "[크롤러] 실시간 예약현황 → 하이코리아 방문예약에서 확인 필요.",
     "source": S_EMINWON},
    {"id": "v_dirty_1", "lang": "ko", "category": "visa", "stratum": "dirty",
     "query": "외국인 등록 며칠안에 해야됨?? 빨리해야하나", "expected_intent": "visa",
     "gold": "90일을 초과해 체류하려는 외국인은 입국일부터 90일 이내 등록. 자격 부여·변경 시에는 즉시.",
     "source": S_REGTIME},

    # ── 건강보험 (insurance) 11 ──
    {"id": "i_indb_1", "lang": "ko", "category": "insurance", "stratum": "in_db",
     "query": "유학생도 건강보험 가입 대상이야?", "expected_intent": "health_insurance",
     "gold": "D-2/D-4 유학생은 국민건강보험 지역가입 적용 대상.", "source": S_DONGAINS},
    {"id": "i_indb_2", "lang": "ko", "category": "insurance", "stratum": "in_db",
     "query": "건강보험은 언제부터 가입되는 거야?", "expected_intent": "health_insurance",
     "gold": "6개월 이상 체류 외국인은 2019년 7월 16일부터 자동으로 지역가입자 당연가입. 별도 신청 없이 공단에서 일괄 처리.",
     "source": S_DONGAINS},
    {"id": "i_indb_3", "lang": "ko", "category": "insurance", "stratum": "in_db",
     "query": "건강보험료는 어떻게 납부해?", "expected_intent": "health_insurance",
     "gold": "자동이체, 가상계좌, 은행, 전자수납, 공단지사(신용카드), 징수포털 등으로 납부. 매월 25일까지 다음 달 보험료 선납.",
     "source": S_DONGAINS},
    {"id": "i_indb_4", "lang": "ko", "category": "insurance", "stratum": "in_db",
     "query": "보험료를 안 내면 어떤 불이익이 있어?", "expected_intent": "health_insurance",
     "gold": "보험급여 제한, 비자연장 등 체류허가 신청 시 불이익, 소득·재산·자동차 등에 대한 법적 징수.",
     "source": S_DONGAINS},
    {"id": "i_cplx_1", "lang": "ko", "category": "insurance", "stratum": "complex",
     "query": "건강보험은 한국 온 지 6개월 지나야 가입되는 거 아니야?", "expected_intent": "health_insurance",
     "gold": "오해. 6개월 이상 체류 시 2019년 7월 16일부터 자동 당연가입. 별도 신청 불필요.",
     "source": S_DONGAINS},
    {"id": "i_cplx_2", "lang": "ko", "category": "insurance", "stratum": "complex",
     "query": "건강보험료 한 달에 얼마야?", "expected_intent": "health_insurance",
     "gold": "2023년 기준 월 71,920원. 정확한 금액은 NHIS 최신 고시(보건복지부고시 제2025-69호) 재확인 필요.",
     "source": S_DONGAINS},
    {"id": "i_cplx_3", "lang": "ko", "category": "insurance", "stratum": "complex",
     "query": "보험료 밀리면 비자 연장에 문제 생겨?", "expected_intent": "health_insurance",
     "gold": "연장 신청 시 체납이 확인되어 원칙적으로 6개월 이하로 제한 연장될 수 있음.", "source": S_IMMARREAR},
    {"id": "i_cplx_4", "lang": "ko", "category": "insurance", "stratum": "complex",
     "query": "학교 보험 안내랑 공단 기준이 다르면 뭘 믿어?", "expected_intent": "health_insurance",
     "gold": "학교(국제교류과)는 가입 확인·납부·미납 불이익을 안내하지만, 일부 수치·시점은 국민건강보험공단 최신 고시로 재확인해야 함.",
     "source": S_DONGAINS},
    {"id": "i_cplx_5", "lang": "ko", "category": "insurance", "stratum": "complex",
     "query": "건강보험으로 안 되는 치료가 있어?", "expected_intent": "health_insurance",
     "gold": "치과, 한방, 미용 치료, 임신·출산 관련 의료비는 보험 적용 제외.", "source": S_DONGAINS},
    {"id": "i_uncov_1", "lang": "ko", "category": "insurance", "stratum": "uncovered",
     "query": "올해 외국인 건강보험 적용 고시 바뀐 거 있어?", "expected_intent": "health_insurance",
     "gold": "[최신고시] 보건복지부고시 제2025-69호(2025-04-23) 등 개정 이력 확인 → NHIS 법령 페이지 최신본으로 재확인 필요.",
     "source": S_NHISLAW},
    {"id": "i_dirty_2", "lang": "ko", "category": "insurance", "stratum": "dirty",
     "query": "보험료 안내면 비자에 영향 감??", "expected_intent": "health_insurance",
     "gold": "연장 신청 시 체납 확인. 미납이면 원칙적으로 6개월 이하 제한 연장 등 불이익.", "source": S_IMMARREAR},

    # ── 아르바이트·시간제취업 (work) 8 ──
    {"id": "w_indb_1", "lang": "ko", "category": "work", "stratum": "in_db",
     "query": "유학생도 아르바이트 할 수 있어?", "expected_intent": "work",
     "gold": "D-2/D-4는 원칙적으로 취업활동 자격이 아니며, 시간제취업은 사전 허가(체류자격외 활동허가)를 받은 범위 안에서만 가능.",
     "source": S_ACTOUT},
    {"id": "w_indb_4", "lang": "ko", "category": "work", "stratum": "in_db",
     "query": "시간제취업 허가는 어디서 신청해?", "expected_intent": "work",
     "gold": "하이코리아 전자민원의 '유학생(D-2)·어학연수생(D-4-1) 시간제취업 허가/신고' 또는 출입국관서 방문.",
     "source": S_EMINWON},
    {"id": "w_indb_5", "lang": "ko", "category": "work", "stratum": "in_db",
     "query": "아르바이트할 때 학교 확인이 필요해?", "expected_intent": "work",
     "gold": "학교 유학생 담당자/지도교수의 확인서가 필요(동아대 제출 흐름).", "source": S_DONGAVISA},
    {"id": "w_cplx_1", "lang": "ko", "category": "work", "stratum": "complex",
     "query": "허가 없이 아르바이트하면 어떻게 돼?", "expected_intent": "work",
     "gold": "무허가 근무·허가조건 위반은 범칙금, 향후 시간제취업 제한, D-10 등 체류자격 변경 제한, 자격 취소·퇴거로 이어질 수 있음.",
     "source": S_ACTOUT},
    {"id": "w_cplx_5", "lang": "ko", "category": "work", "stratum": "complex",
     "query": "알바 자리를 바꾸면 허가를 다시 받아야 해?", "expected_intent": "work",
     "gold": "시간제취업은 허가받은 범위 안에서만 가능하므로, 근무처·조건이 바뀌면 허가조건 위반이 되지 않도록 재허가/신고가 필요.",
     "source": S_ACTOUT},
    {"id": "w_cplx_6", "lang": "ko", "category": "work", "stratum": "complex",
     "query": "졸업하고 취업하려면 비자를 어떻게 해야 해?", "expected_intent": "work",
     "gold": "구직(D-10) 등으로 변경을 검토. 단 시간제취업 위반 이력이 있으면 D-10 등 변경이 제한될 수 있음.",
     "source": S_ACTOUT},
    {"id": "w_uncov_1", "lang": "ko", "category": "work", "stratum": "uncovered",
     "query": "이번 학기 시간제취업 학교 확인 신청 마감 언제야?", "expected_intent": "work",
     "gold": "[크롤러] 학기별 공지 → 동아대 국제교류과 안내 확인 필요.", "source": S_DONGAVISA},
    {"id": "w_dirty_2", "lang": "ko", "category": "work", "stratum": "dirty",
     "query": "알바 허가 없이 그냥 하면 어케됨?", "expected_intent": "work",
     "gold": "범칙금, 향후 시간제취업 제한, D-10 변경 제한, 자격 취소·퇴거 등 불이익.", "source": S_ACTOUT},

    # ── 국제교류과·학교서류 (admin) 6 ──
    {"id": "a_indb_1", "lang": "ko", "category": "admin", "stratum": "in_db",
     "query": "D-4에서 D-2로 비자 바꿀 때 재정능력 증빙은 얼마야?",
     "expected_intent": "academic",
     "gold": "본교 어학연수생의 경우 재정능력입증서 800만원 이상, 일반의 경우 1,600만원 이상.",
     "source": S_DONGAVISA},
    {"id": "a_indb_2", "lang": "ko", "category": "admin", "stratum": "in_db",
     "query": "국제교류과는 어떤 걸 도와줘?", "expected_intent": "academic",
     "gold": "외국인 유학생 지원 메뉴로 기숙사, 보험, VISA 정보, 기타 대학생활을 안내.", "source": S_DONGAINTL},
    {"id": "a_indb_3", "lang": "ko", "category": "admin", "stratum": "in_db",
     "query": "비자 서류에 필요한 학교 확인서는 누가 발급해줘?", "expected_intent": "academic",
     "gold": "국제교류과/유학생 담당자가 체류·시간제취업 관련 학교 확인서·제출서류를 안내·확인.", "source": S_DONGAVISA},
    {"id": "a_cplx_1", "lang": "ko", "category": "admin", "stratum": "complex",
     "query": "학교 서류랑 출입국 서류 중 뭘 먼저 준비해?", "expected_intent": "academic",
     "gold": "시간제취업은 학교 확인서를 먼저 받은 뒤 하이코리아/출입국에 신청하는 순서. 비자에 영향 주는 사안은 국제교류과·출입국에 먼저 확인.",
     "source": S_DONGAVISA},
    {"id": "a_cplx_2", "lang": "ko", "category": "admin", "stratum": "complex",
     "query": "비자 문제는 국제교류과랑 출입국 중 어디에 먼저 물어봐?", "expected_intent": "academic",
     "gold": "학사·학교서류는 국제교류과, 법정 기준·심사는 하이코리아/1345/부산출입국이 우선. 사안에 따라 양쪽 확인 권장.",
     "source": S_DONGAINTL},
    {"id": "a_uncov_1", "lang": "ko", "category": "admin", "stratum": "uncovered",
     "query": "국제교류과 이번 주 상담 가능한 시간 알려줘", "expected_intent": "academic",
     "gold": "[크롤러] 운영시간·공지는 국제교류과 페이지에서 최신 확인 필요.", "source": S_DONGAINTL},

    # ── 장학금 (scholarship) 7 ──
    {"id": "s_indb_1", "lang": "ko", "category": "scholarship", "stratum": "in_db",
     "query": "외국인 유학생 장학금은 어떤 종류가 있어?", "expected_intent": "academic",
     "gold": "학부 한국어트랙·영어트랙, 대학원 한국어트랙·영어트랙 장학이 운영됨.", "source": S_SCH_KR_UG},
    {"id": "s_indb_2", "lang": "ko", "category": "scholarship", "stratum": "in_db",
     "query": "신입생 한국어트랙 장학금 기준이 뭐야?", "expected_intent": "academic",
     "gold": "신입생 TOPIK 기준 장학, 한국어학당 수료자 장학, 재학생 성적우수 장학으로 구성.", "source": S_SCH_KR_UG},
    {"id": "s_indb_3", "lang": "ko", "category": "scholarship", "stratum": "in_db",
     "query": "영어트랙은 어떤 영어성적으로 장학금을 받아?", "expected_intent": "academic",
     "gold": "IELTS/TOEFL/New TEPS 기준의 신입생 장학과 재학생 성적 장학.", "source": S_SCH_EN_UG},
    {"id": "s_indb_4", "lang": "ko", "category": "scholarship", "stratum": "in_db",
     "query": "대학원 유학생 장학금 유지 조건은?", "expected_intent": "academic",
     "gold": "대학원 한국어트랙은 TOPIK/영어성적/학업성적 85점 이상 유지 조건으로 수업료 감면.", "source": S_SCH_KR_GR},
    {"id": "s_cplx_1", "lang": "ko", "category": "scholarship", "stratum": "complex",
     "query": "성적이 떨어지면 장학금이 끊겨?", "expected_intent": "academic",
     "gold": "대학원은 학업성적 85점 이상 유지가 조건이라 미달 시 감면이 영향받을 수 있음(트랙별 기준 확인).",
     "source": S_SCH_KR_GR},
    {"id": "s_cplx_2", "lang": "ko", "category": "scholarship", "stratum": "complex",
     "query": "한국어트랙이랑 영어트랙 장학 기준이 어떻게 달라?", "expected_intent": "academic",
     "gold": "한국어트랙은 TOPIK 기준, 영어트랙은 IELTS/TOEFL/New TEPS 기준으로 산정.", "source": S_SCH_EN_UG},
    {"id": "s_uncov_1", "lang": "ko", "category": "scholarship", "stratum": "uncovered",
     "query": "이번 학기 장학금 신청은 언제까지야?", "expected_intent": "academic",
     "gold": "[크롤러] 학기별 공지 → 국제교류과 장학 페이지 확인 필요.", "source": S_SCH_KR_UG},

    # ── 휴학·복학·수강신청·등록 (academic) 9 ──
    {"id": "ac_indb_1", "lang": "ko", "category": "academic", "stratum": "in_db",
     "query": "휴학은 어떻게 신청해?", "expected_intent": "academic",
     "gold": "일반·군·창업·육아 휴학 신청이 가능하며 최대 휴학기간·등록금 이월 규정이 있음.", "source": S_LOA},
    {"id": "ac_indb_2", "lang": "ko", "category": "academic", "stratum": "in_db",
     "query": "신입생도 첫 학기에 휴학할 수 있어?", "expected_intent": "academic",
     "gold": "신입생 첫 학기 휴학에는 제한이 있음(학칙 확인).", "source": S_LOA},
    {"id": "ac_indb_3", "lang": "ko", "category": "academic", "stratum": "in_db",
     "query": "복학은 어떻게 신청해?", "expected_intent": "academic",
     "gold": "일반복학·군복학은 인터넷으로 신청. 미복학 시 제적됨.", "source": S_RETURN},
    {"id": "ac_indb_5", "lang": "ko", "category": "academic", "stratum": "in_db",
     "query": "등록금은 어떻게 납부해?", "expected_intent": "academic",
     "gold": "등록금 고지서 출력 후 가상계좌 또는 카드납부로 납부.", "source": S_TUITION},
    {"id": "ac_cplx_1", "lang": "ko", "category": "academic", "stratum": "complex",
     "query": "등록금 안 내면 제적돼?", "expected_intent": "academic",
     "gold": "미등록(등록금 미납) 시 제적. 유학생은 등록 상태가 D-2 체류자격 유지와 직결되므로 국제교류과·출입국에 즉시 확인 필요.",
     "source": S_RETURN},
    {"id": "ac_cplx_2", "lang": "ko", "category": "academic", "stratum": "complex",
     "query": "복학하면 바로 수강신청 할 수 있어?", "expected_intent": "academic",
     "gold": "복학으로 재학 상태가 된 뒤 등록금 납부·수강신청이 가능.", "source": S_RETURN},
    {"id": "ac_cplx_3", "lang": "ko", "category": "academic", "stratum": "complex",
     "query": "휴학이 비자에 영향을 줘?", "expected_intent": "academic",
     "gold": "휴학·미등록·장기결석·초과학기·졸업유예는 D-2 체류기간 연장·유지에 영향을 줄 수 있어 국제교류과·출입국에 먼저 확인.",
     "source": S_DONGAINTL},
    {"id": "ac_uncov_1", "lang": "ko", "category": "academic", "stratum": "uncovered",
     "query": "이번 학기 수강신청 날짜 알려줘", "expected_intent": "academic",
     "gold": "[크롤러] 학기별 수강신청 공지(교체형) → 동아대 학사 안내 최신 페이지 확인 필요.", "source": S_ENROLL},
    {"id": "ac_uncov_2", "lang": "ko", "category": "academic", "stratum": "uncovered",
     "query": "이번 학기 등록금 납부 마감일 언제야?", "expected_intent": "academic",
     "gold": "[크롤러] 학기별 등록 안내(교체형) → 동아대 등록 안내 최신 페이지 확인 필요.", "source": S_TUITION},

    # ── 기숙사 (housing) 8 ──
    {"id": "h_indb_1", "lang": "ko", "category": "housing", "stratum": "in_db",
     "query": "외국인 유학생 전용 기숙사가 어디야?", "expected_intent": "housing",
     "gold": "석당 글로벌하우스가 외국인 유학생 전용 기숙사로 부민캠퍼스 인근에 위치.", "source": S_DONGAINTL},
    {"id": "h_indb_2", "lang": "ko", "category": "housing", "stratum": "in_db",
     "query": "석당 글로벌하우스는 몇 인 1실이고 정원이 얼마야?", "expected_intent": "housing",
     "gold": "2인 1실, 최대 184명.", "source": S_DONGAINTL},
    {"id": "h_indb_3", "lang": "ko", "category": "housing", "stratum": "in_db",
     "query": "한림생활관은 어느 캠퍼스에 있어?", "expected_intent": "housing",
     "gold": "승학캠퍼스 내에 위치, 2인 1실, 1,019명 규모.", "source": S_DONGAINTL},
    {"id": "h_indb_4", "lang": "ko", "category": "housing", "stratum": "in_db",
     "query": "기숙사 신청은 어디서 해?", "expected_intent": "housing",
     "gold": "석당 글로벌하우스는 globalhouse.donga.ac.kr, 한림생활관은 hanlim.donga.ac.kr에서 각 학기 신청 공지 확인. 국제교류과에서도 안내.",
     "source": S_DONGAINTL},
    {"id": "h_cplx_1", "lang": "ko", "category": "housing", "stratum": "complex",
     "query": "부민캠퍼스 다니는데 승학캠퍼스 한림생활관에 들어갈 수 있어?", "expected_intent": "housing",
     "gold": "한림생활관은 승학캠퍼스 소재이고 외국인 유학생 전용은 부민 인근 석당 글로벌하우스 → 캠퍼스·전용 분류를 공지로 확인 필요.",
     "source": S_DONGAINTL},
    {"id": "h_cplx_2", "lang": "ko", "category": "housing", "stratum": "complex",
     "query": "외국인 유학생은 기숙사 우선 배정이 돼?", "expected_intent": "housing",
     "gold": "석당 글로벌하우스가 '외국인 유학생 전용'이라는 점이 가장 중요한 우선 분류. 세부 우선순위는 고정 표기가 없어 학기별 공지 확인 필요.",
     "source": S_DONGAINTL},
    {"id": "h_uncov_1", "lang": "ko", "category": "housing", "stratum": "uncovered",
     "query": "이번 학기 석당 글로벌하우스 입사 신청 언제까지야?", "expected_intent": "housing",
     "gold": "[크롤러] 학기별 입사 공지 → 석당 글로벌하우스 페이지 확인 필요.", "source": S_GLOBALHS},
    {"id": "h_uncov_2", "lang": "ko", "category": "housing", "stratum": "uncovered",
     "query": "다음 학기 한림생활관 모집 공고 떴어?", "expected_intent": "housing",
     "gold": "[크롤러] 입사 공지·신청 기간 → 한림생활관 페이지 확인 필요.", "source": S_HANLIM},

    # ── 은행·금융 (bank) 2 ──
    {"id": "b_indb_3", "lang": "ko", "category": "bank", "stratum": "in_db",
     "query": "모바일 외국인등록증으로 어느 은행에서 비대면 업무를 볼 수 있어?", "expected_intent": "bank",
     "gold": "전북은행에서 비대면 업무 처리 가능. 신한·하나·아이엠뱅크·부산·전북·제주 6개 은행에서 대면 업무 가능(2025.3.21~).",
     "source": S_BANKNEWS},
    {"id": "b_uncov_1", "lang": "ko", "category": "bank", "stratum": "uncovered",
     "query": "요즘 모바일 외국인등록증으로 계좌 개설 되는 은행 어디야?", "expected_intent": "bank",
     "gold": "[최신] 2025-03-21부터 등록외국인은 모바일 외국인등록증으로 6개 은행에서 금융업무 가능(대면 가능 은행에 부산은행 포함). 최신 대상 은행은 보도자료로 재확인.",
     "source": S_BANKNEWS},

    # ── 유심·핸드폰 (telecom) 4 ──
    {"id": "t_indb_1", "lang": "ko", "category": "telecom", "stratum": "in_db",
     "query": "외국인 후불 핸드폰 개통할 때 체류코드마다 다른 게 있어?", "expected_intent": "telecom",
     "gold": "체류코드에 따라 개통 가능 대수, 할부 구매 가능 여부, 보증금 면제 등 세부사항이 달라짐. 가입 전 통신사에 확인 필요.",
     "source": S_KOTRATEL},
    {"id": "t_indb_2", "lang": "ko", "category": "telecom", "stratum": "in_db",
     "query": "후불 핸드폰 개통하려면 뭐가 필요해?", "expected_intent": "telecom",
     "gold": "외국인등록증 또는 국내 거소신고증 지참, 본인 명의 통장 또는 신용카드로만 납부 가능.",
     "source": S_KOTRATEL},
    {"id": "t_cplx_1", "lang": "ko", "category": "telecom", "stratum": "complex",
     "query": "외국인등록증 없이 후불 핸드폰 개통 가능해?", "expected_intent": "telecom",
     "gold": "후불 개통 시 외국인등록증 또는 국내 거소신고증이 필수. 등록증 없이는 후불 개통 불가.",
     "source": S_KOTRATEL},
    {"id": "t_dirty_1", "lang": "ko", "category": "telecom", "stratum": "dirty",
     "query": "핸드폰 개통 뭐 필요함?", "expected_intent": "telecom",
     "gold": "후불 개통 시 외국인등록증/거소신고증과 본인 명의 통장·카드 필요.",
     "source": S_KOTRATEL},

    # ── 부산 지원기관·생활 (support) 4 ──
    {"id": "sp_indb_1", "lang": "ko", "category": "support", "stratum": "in_db",
     "query": "1345는 무슨 번호야?", "expected_intent": "support",
     "gold": "외국인종합안내센터. 20개 언어로 출입국 민원·생활편의 안내(국내 1345, 해외 +82-2-1345).", "source": S_IMM1345},
    {"id": "sp_indb_2", "lang": "ko", "category": "support", "stratum": "in_db",
     "query": "부산 외국인 통합콜센터 번호 알려줘", "expected_intent": "support",
     "gold": "1600-0051. 8개 언어로 체류·행정·근로·생활 전반 상담, 일~금 09:00~18:00.", "source": S_BUSANCALL},
    {"id": "sp_indb_3", "lang": "ko", "category": "support", "stratum": "in_db",
     "query": "통역으로 상담받을 수 있는 곳이 있어?", "expected_intent": "support",
     "gold": "1345(20개 언어), 부산 외국인 통합콜센터(1600-0051, 8개 언어), 부산외국인주민지원센터 등에서 통·번역 상담 제공.",
     "source": S_BUSANSUP},
    {"id": "sp_cplx_1", "lang": "ko", "category": "support", "stratum": "complex",
     "query": "출입국 관련 무료 법률·통역 상담을 받을 수 있어?", "expected_intent": "support",
     "gold": "부산글로벌도시재단·부산외국인주민지원센터에서 법률·노무·출입국 전문상담을 제공하고, 1345는 공공기관 3자 통역·마을변호사 통역을 안내.",
     "source": S_BUSANSUP},
]

if __name__ == "__main__":
    from collections import Counter
    print("총", len(EVAL_QUERIES), "문항")
    print("stratum:", dict(Counter(q["stratum"] for q in EVAL_QUERIES)))
    print("category:", dict(Counter(q["category"] for q in EVAL_QUERIES)))
    print("lang:", dict(Counter(q["lang"] for q in EVAL_QUERIES)))
