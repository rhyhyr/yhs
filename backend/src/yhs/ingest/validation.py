"""
yhs/ingest/validation.py

추출 결과를 그래프에 넣기 전에 검사한다.

프롬프트로 규칙을 주는 것만으로는 부족하다. 로컬 모델은 지시를 자주 어기고,
어긴 결과가 그대로 들어가면 그래프가 조용히 망가진다. 실제로 이런 관계가
들어가 있었다:

    부산1호선 중앙동역 -[PRECEDES]-> 김해국제공항   (교통 안내를 절차로 오인)
    경상남도 양산시   -[BLOCKS]-> 출입국·외국인청    (관할 구역을 차단 관계로)

여기서 거르는 것:
  1. endpoint 누락   관계의 subject/object 가 같은 응답의 엔티티에 없음
  2. 타입 조합 위반  predicate 가 요구하는 subject/object 타입이 아님
  3. 설명성 문단     기관 소개·주소·연락처 문단에서 만든 절차 관계
  4. 금지 엔티티     일반명사·국가명·날짜 단독·문장 조각
  5. 이름 표기 흔들림 '사업자등록증사본' 과 '사업자등록증 사본'
"""

from __future__ import annotations

import re

from yhs.ingest.stats import STATS
from yhs.schema.types import EntityNode, Triple

# ── 엔티티 타입 ──────────────────────────────────────────────────────────────
ENTITY_TYPES = {
    "PROCEDURE",     # 외국인등록, 체류기간연장허가
    "DOCUMENT",      # 여권, 외국인등록증
    "CONDITION",     # 입국 후 90일 이내, TOPIK 3급 이상
    "ORGANIZATION",  # 출입국·외국인청, 국민건강보험공단
    "VISA",          # D-2, F-5 (체류자격 코드 자체)
    "PRODUCT",       # 장학금, 기숙사, 건강보험
    "PERSON_GROUP",  # 외국인, 유학생, D-2 소지자 (적용·발급 대상 집단)
}

# ── predicate 별 허용 타입 조합 ──────────────────────────────────────────────
# None 은 제한 없음.
PREDICATE_TYPES: dict[str, tuple[set[str] | None, set[str] | None]] = {
    # PRODUCT 를 REQUIRES 의 subject 로 허용한다.
    #   유선전화 및 인터넷 -[REQUIRES]-> 여권   (개통에 필요한 서류)
    # 제도·서비스를 신청할 때 내는 서류는 절차의 서류와 성격이 같다.
    "REQUIRES":          ({"PROCEDURE", "VISA", "PRODUCT"},
                          {"DOCUMENT", "CONDITION", "PROCEDURE"}),
    # DOCUMENT 와 PERSON_GROUP 을 HAS_CONDITION 의 subject 로 허용한다.
    #   재정능력입증서 -[HAS_CONDITION]-> 1600만원 이상   (서류가 갖춰야 할 요건)
    #   17세 미만 등록 외국인 -[HAS_CONDITION]-> 17세가 된 때 90일 이내
    # object 는 여전히 CONDITION 만이므로 기관·서류가 조건 자리에 오지는 못한다.
    "HAS_CONDITION":     ({"PROCEDURE", "VISA", "PRODUCT",
                           "DOCUMENT", "PERSON_GROUP"}, {"CONDITION"}),
    "HAS_EXCEPTION":     ({"PROCEDURE", "VISA", "CONDITION"}, {"CONDITION", "PERSON_GROUP"}),
    "BLOCKS":            ({"CONDITION"}, {"PROCEDURE", "VISA"}),
    "ENABLES":           ({"DOCUMENT", "CONDITION", "PROCEDURE"}, {"PROCEDURE", "VISA"}),
    "PRECEDES":          ({"PROCEDURE", "VISA"}, {"PROCEDURE", "VISA"}),
    "FOLLOWED_BY":       ({"PROCEDURE", "VISA"}, {"PROCEDURE", "VISA"}),
    "CAN_TRANSITION_TO": ({"VISA"}, {"VISA"}),
    "ISSUED_BY":         ({"DOCUMENT", "VISA"}, {"ORGANIZATION"}),
    "ISSUED_TO":         ({"DOCUMENT", "VISA"}, {"PERSON_GROUP"}),
    "SUBMITTED_TO":      ({"DOCUMENT", "PROCEDURE"}, {"ORGANIZATION"}),
    "APPLIES_TO":        ({"PROCEDURE", "VISA", "PRODUCT"},
                          {"PERSON_GROUP", "CONDITION", "VISA"}),
    "PRODUCES":          ({"PROCEDURE"}, {"DOCUMENT", "VISA"}),
    "RELATED_TO":        (None, None),
}

# 절차 관계 — 설명성 문단에서는 만들지 않는다.
PROCEDURAL_PREDICATES = {
    "REQUIRES", "PRECEDES", "FOLLOWED_BY", "BLOCKS", "ENABLES",
    "HAS_CONDITION", "HAS_EXCEPTION", "CAN_TRANSITION_TO", "PRODUCES",
}

# 설명성 문단에서 남길 관계.
#
# 처음에는 절차 술어만 막고 RELATED_TO 는 통과시켰다. 그랬더니 '오시는 길'
# 문서 하나가 RELATED_TO 48건을 만들어 냈다 — 검찰청 목록에서
# '광주지방검찰청 -[RELATED_TO]-> 광주고등검찰청' 같은 것들이다.
# 검증 통과 관계의 절반이 이런 식이 되면, 엔티티에서 1~2홉 확장하는
# 검색에서 무관한 기관으로 새어 나간다.
#
# 기관 소개·주소 문단에서 쓸 만한 것은 '어디서 발급/제출하는가' 뿐이다.
DESCRIPTIVE_ALLOWED_PREDICATES = {"ISSUED_BY", "SUBMITTED_TO"}

# 문단 유형 화이트리스트.
# 모델이 "description", "scholarship" 처럼 목록 밖 값을 지어내는 일이 잦다.
# 목록 밖이면 descriptive 로 보수적으로 떨어뜨린다 — 절차 관계를 막는 쪽이
# 안전하기 때문이다. 반대로 두면 설명성 문단 차단이 통째로 무력화된다.
CHUNK_TYPES = {"procedural", "requirement", "policy",
               "descriptive", "location", "contact", "listing"}

# 관계 추출 가치가 낮은 문단 유형.
#
# listing 은 여기서 뺐다. 147청크 전수 적재에서 103건이 listing 으로 분류돼
# 관계 252건이 막혔는데, 그 안에
#   등록사항 변경 신고 -[REQUIRES]-> 여권
#   은행잔고증명서 -[HAS_CONDITION]-> 신청일 기준 30일 이내 발급한 것
# 처럼 그래프의 핵심이 되어야 할 것들이 섞여 있었다. 서류 목록 문단이
# "나열되어 있다"는 이유로 listing 이 된 탓이다.
#
# 막으려던 노이즈(검찰청 목록의 기관끼리 RELATED_TO 48건)는 location 과
# descriptive 에서 나왔지 listing 에서 나온 것이 아니다.
DESCRIPTIVE_CHUNK_TYPES = {"descriptive", "location", "contact"}


# 설명성·목록 문단에서 나왔고 어떤 채택 관계에도 참여하지 않는 ORGANIZATION 은
# 그래프 노드로 만들지 않는다.
#
# 근거 (147청크 전수):
#   고유 기관 312개 중 264개(85%)가 채택 관계에 한 번도 참여하지 않았다.
#   그중 237개는 설명성·목록 문단에서만 나왔고, 98%는 청크 본문에 그대로
#   들어 있다. 즉 벡터·키워드 검색으로 이미 닿는다.
#   ORGANIZATION 생성량의 77.5%가 listing 문단이고, 네 문서
#   (소속기관·기관소개·종합안내센터·오시는 길)가 1,133개를 만든다.
#   전국 검찰청 목록이 대표적이다 — 노드로 두어도 확장할 엣지가 없다.
#
# 즉 검색에 필요한 것은 '이름이 본문에 있다'이지 '그래프에 노드가 있다'가
# 아니다. 관계를 가진 기관은 어느 문단에서 나왔든 그대로 남는다.
DROP_UNUSED_ORG_IN_DESCRIPTIVE = True
_ORG_HOST_CHUNK_TYPES = DESCRIPTIVE_CHUNK_TYPES | {"listing"}


def normalize_chunk_type(raw: str) -> tuple[str, bool]:
    """(정규화된 유형, 목록 밖이었는지) 를 돌려준다."""
    c = (raw or "").strip().lower()
    if c in CHUNK_TYPES:
        return c, False
    return "descriptive", True

# ── 엔티티로 만들면 안 되는 것 ───────────────────────────────────────────────
_GENERIC_NOUNS = {
    "처리", "안내", "문의", "내용", "방법", "이용", "지원", "정보", "서비스",
    "확인", "신청자", "대상", "경우", "관련", "기타", "사항", "업무", "참고",
    "제공", "운영", "관리", "사용", "필요", "가능",
}
_COUNTRY_NAMES = {
    "미국", "영국", "호주", "캐나다", "뉴질랜드", "아일랜드", "중국", "일본",
    "베트남", "몽골", "네팔", "인도", "필리핀", "태국", "러시아", "독일",
    "프랑스", "스페인", "남아프리카공화국", "싱가포르", "말레이시아",
    "Australia", "America", "Canada",
}
# 날짜·숫자 단독
_DATE_ONLY_RE = re.compile(r"^\d{1,4}[년./-]?\s*\d{0,2}[월./-]?\s*\d{0,2}일?$")
_NUMBER_ONLY_RE = re.compile(r"^[\d.,%]+$")
# 영어 snake_case 조어 (한글이 하나도 없고 밑줄이 있는 것)
_SNAKE_EN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*(_[A-Za-z0-9]+)+$")
# 문장 조각
_SENTENCE_TAIL_RE = re.compile(r"[.。]$|[다요함음]\.?$")

# ── 긴 이름: 고유명사인가 문장인가 ───────────────────────────────────────────
#
# 처음에는 30자를 넘으면 무조건 잘랐다. 그랬더니
#   International Student Academic Excellence Scholarships A, B, C, D
#   부산 Support Center for Foreign Workers
#   장기체류 재외국민 및 외국인에 대한 건강보험 적용기준 고시
# 같은 정상적인 제도명·기관명이 통째로 사라졌고, 그 이름을 쓰던 관계까지
# endpoint 누락으로 연쇄 유실됐다 (64건 중 대부분).
#
# 길이만으로는 못 가른다. 상한은 '이 길이를 넘으면 무엇이든 문장'인 선까지만
# 올리고(75자), 그 아래는 문장인지 따로 본다.
_MAX_NAME_LEN = 75

# 한국어: 어절이 많으면 문장이다.
#   '장기체류 재외국민 및 외국인에 대한 건강보험 적용기준 고시'        8어절 → 이름
#   '통계청이 고시한 표준직업분류의 대분류 1 또는 2번 직종 종사자'      9어절 → 문장
_MAX_KO_WORDS = 9

# 영어: 기능어가 섞이면 문장이다. 고유명사는 명사만 이어 붙는다.
#   'International Student Academic Excellence Scholarships'  기능어 0 → 이름
#   'The specific details of eligibility and benefits may change'  4 → 문장
_EN_FUNCTION_WORDS = {
    "the", "of", "and", "or", "but", "who", "which", "that", "at", "in",
    "on", "as", "while", "may", "do", "not", "both", "if", "when", "with",
    "from", "than", "their", "your", "this", "these", "are", "is", "be",
}
_MIN_EN_FUNCTION_WORDS = 3

# 진행형이 둘 이상이면 서술문이다.
#   'Current students working part-time while studying' → working, studying
_EN_GERUND_RE = re.compile(r"\b[a-z]+ing\b")
_MIN_EN_GERUNDS = 2

_HANGUL_RE = re.compile(r"[가-힣]")


def _looks_like_sentence(name: str) -> str | None:
    """이름이 아니라 문장·구절로 보이면 그 사유를 돌려준다."""
    if len(name) > _MAX_NAME_LEN:
        return f"문장 조각({_MAX_NAME_LEN}자 초과)"

    if _HANGUL_RE.search(name):
        if len(name.split()) >= _MAX_KO_WORDS:
            return "문장 조각(어절 과다)"
        if name.count(",") >= 3:
            return "문장 조각(나열)"
        return None

    # 한글이 없으면 영어 이름으로 본다.
    # 고유명사는 대문자로 시작한다. 소문자로 시작하면 문장에서 잘라낸 조각이다.
    #   'departments offering both Korean and English courses' → 조각
    #   'International Student Academic Excellence Scholarships' → 이름
    if name[:1].islower():
        return "문장 조각(소문자 시작)"

    words = [w.strip(".,()'\"").lower() for w in name.split()]
    if sum(1 for w in words if w in _EN_FUNCTION_WORDS) >= _MIN_EN_FUNCTION_WORDS:
        return "문장 조각(영어 기능어 과다)"
    if len(_EN_GERUND_RE.findall(name)) >= _MIN_EN_GERUNDS:
        return "문장 조각(영어 서술문)"
    return None

# PRODUCT 로 잘못 분류되는 명백한 노이즈만 막는다.
# 모델이 애매한 것을 전부 PRODUCT 로 밀어 넣는 경향이 있다
# (버스 5-1번, 체납액, 전자납부번호 …). 과도한 하드코딩은 피하고
# 교통편·금액·번호처럼 확실한 것만 잡는다.
_PRODUCT_NOISE_RE = re.compile(
    r"^(버스|지하철|전철|택시)\s|"
    r"^\S*\d+\s*번$|"          # 5-1번, 109번
    r"(번호|금액|요금|수수료|비용)$"
)


def normalize_name(name: str) -> str:
    """표기 흔들림을 흡수한 비교용 키.

    공백만 제거한다. 과병합을 막기 위해 조사·괄호까지는 건드리지 않는다.
    '사업자등록증사본' 과 '사업자등록증 사본' 은 같은 키가 되지만,
    '외국인등록' 과 '외국인등록증' 은 여전히 다르다.
    """
    return re.sub(r"\s+", "", (name or "").strip())


def is_blocked_entity(name: str, etype: str) -> str | None:
    """엔티티로 만들면 안 되는 이름이면 그 사유를, 괜찮으면 None 을 돌려준다."""
    n = (name or "").strip()
    if not n:
        return "이름 없음"
    sentence = _looks_like_sentence(n)
    if sentence:
        return sentence
    if _SNAKE_EN_RE.match(n):
        return "영어 snake_case 조어"
    if _NUMBER_ONLY_RE.match(n):
        return "숫자 단독"
    if _DATE_ONLY_RE.match(n):
        return "날짜 단독"
    if _SENTENCE_TAIL_RE.search(n) and " " in n:
        return "문장 조각"
    if etype == "PRODUCT" and _PRODUCT_NOISE_RE.search(n):
        return "PRODUCT 오분류(교통·금액·번호)"

    # 일반명사·국가명은 CONDITION 으로 쓰일 때만 예외적으로 허용한다.
    if etype != "CONDITION":
        if n in _GENERIC_NOUNS:
            return "일반 명사"
        if n in _COUNTRY_NAMES:
            return "국가명"
    return None


def validate(
    entities: list[EntityNode],
    triples: list[Triple],
    chunk_type: str = "",
    trace: list[dict] | None = None,
) -> tuple[list[EntityNode], list[Triple]]:
    """한 청크의 추출 결과를 검사해 살아남은 것만 돌려준다.

    프롬프트가 규칙을 어겨도 여기서 막힌다. 무엇이 왜 걸러졌는지는 전부
    STATS 에 남아 인제스트 끝 요약에 나온다.

    trace 를 주면 항목별 판정(무엇이 왜 남고 왜 버려졌는지)을 거기에 쌓는다.
    분석 스크립트가 쓴다 — 분석용으로 같은 로직을 따로 짜면 실제 적재와
    어긋나므로, 한 함수만 두고 관찰만 덧붙인다. 적재 경로는 trace 를 주지
    않으므로 동작이 달라지지 않는다.
    """
    def _rec(**kw) -> None:
        if trace is not None:
            trace.append(kw)
    ctype, was_unknown = normalize_chunk_type(chunk_type)
    if was_unknown and (chunk_type or "").strip():
        STATS.chunk_type_unknown += 1
        STATS.unknown_chunk_types[(chunk_type or "").strip().lower()] += 1

    # ── 1) 엔티티 선별 ───────────────────────────────────────────────────
    kept: list[EntityNode] = []
    by_key: dict[str, EntityNode] = {}
    for e in entities:
        etype = (e.type or "").strip().upper()
        if etype and etype not in ENTITY_TYPES:
            STATS.entity_type_invalid += 1
            STATS.invalid_entity_types[etype] += 1
            _rec(kind="entity", verdict="dropped", reason="타입 무효",
                 name=e.name, type=etype)
            continue

        reason = is_blocked_entity(e.name, etype)
        if reason:
            STATS.entity_blocked += 1
            STATS.entity_block_reasons[reason] += 1
            _rec(kind="entity", verdict="dropped", reason=reason,
                 name=e.name, type=etype)
            continue

        key = normalize_name(e.name)
        prev = by_key.get(key)
        if prev is None:
            e.type = etype
            by_key[key] = e
            kept.append(e)
            _rec(kind="entity", verdict="kept", reason="",
                 name=e.name, type=etype)
        else:
            # 표기만 다른 같은 개념. 먼저 온 것을 남기고 빈 칸만 채운다.
            STATS.entity_name_merged += 1
            _rec(kind="entity", verdict="merged", reason="표기 병합",
                 name=e.name, type=etype, merged_into=prev.name)
            if not prev.type and etype:
                prev.type = etype
            if not prev.summary and e.summary:
                prev.summary = e.summary

    name_to_type = {normalize_name(e.name): (e.type or "") for e in kept}

    # ── 2) 관계 선별 ─────────────────────────────────────────────────────
    kept_triples: list[Triple] = []
    for t in triples:
        s_key = normalize_name(t.subject_id)
        o_key = normalize_name(t.object_id)

        # 2-1) endpoint 가 이 청크의 엔티티에 있어야 한다
        missing = [
            raw for raw, key in ((t.subject_id, s_key), (t.object_id, o_key))
            if key not in name_to_type
        ]
        if missing:
            STATS.relation_orphan_endpoint += 1
            STATS.orphan_endpoint_names.update(missing)
            _rec(kind="relation", verdict="dropped", reason="endpoint 누락",
                 subject=t.subject_id, predicate=t.predicate,
                 object=t.object_id, missing=missing)
            continue

        # 2-2) 설명성 문단에서는 발급·제출 관계만 남긴다
        if (ctype in DESCRIPTIVE_CHUNK_TYPES
                and t.predicate not in DESCRIPTIVE_ALLOWED_PREDICATES):
            STATS.relation_descriptive_blocked += 1
            STATS.descriptive_blocked_samples.append(
                f"[{ctype}] {t.subject_id} -[{t.predicate}]-> {t.object_id}"
            ) if len(STATS.descriptive_blocked_samples) < 15 else None
            _rec(kind="relation", verdict="dropped", reason="설명성 문단 차단",
                 subject=t.subject_id, predicate=t.predicate,
                 object=t.object_id, chunk_type=ctype)
            continue

        # 2-3) 타입 조합 검사
        allowed = PREDICATE_TYPES.get(t.predicate)
        if allowed:
            s_ok, o_ok = allowed
            s_type, o_type = name_to_type[s_key], name_to_type[o_key]
            bad = (s_ok and s_type not in s_ok) or (o_ok and o_type not in o_ok)
            if bad:
                STATS.relation_type_mismatch += 1
                STATS.type_mismatch_samples.append(
                    f"{t.subject_id}({s_type or '?'}) -[{t.predicate}]-> "
                    f"{t.object_id}({o_type or '?'})"
                ) if len(STATS.type_mismatch_samples) < 15 else None
                _rec(kind="relation", verdict="dropped", reason="타입 불일치",
                     subject=t.subject_id, predicate=t.predicate,
                     object=t.object_id,
                     subject_type=s_type or "?", object_type=o_type or "?")
                continue

        # 2-4) 근거 구절이 없으면 버린다
        if not getattr(t, "evidence", "").strip():
            STATS.relation_no_evidence += 1
            _rec(kind="relation", verdict="dropped", reason="근거 없음",
                 subject=t.subject_id, predicate=t.predicate, object=t.object_id)
            continue

        kept_triples.append(t)
        _rec(kind="relation", verdict="kept", reason="",
             subject=t.subject_id, predicate=t.predicate, object=t.object_id,
             subject_type=name_to_type[s_key], object_type=name_to_type[o_key])

    # ── 3) 엣지 없는 기관 노드 정리 ──────────────────────────────────────
    if DROP_UNUSED_ORG_IN_DESCRIPTIVE and ctype in _ORG_HOST_CHUNK_TYPES:
        used = set()
        for t in kept_triples:
            used.add(normalize_name(t.subject_id))
            used.add(normalize_name(t.object_id))
        survivors = []
        for e in kept:
            if (e.type or "") == "ORGANIZATION" and normalize_name(e.name) not in used:
                STATS.entity_blocked += 1
                STATS.entity_block_reasons["기관 노드(관계 없음, 본문 검색으로 대체)"] += 1
                _rec(kind="entity", verdict="dropped",
                     reason="기관 노드(관계 없음, 본문 검색으로 대체)",
                     name=e.name, type=e.type)
                continue
            survivors.append(e)
        kept = survivors

    if ctype:
        STATS.chunk_types[ctype] += 1
    return kept, kept_triples
