"""
yhs/ingest/llm/prompts.py

추출 프롬프트 한 벌. 모든 provider 가 여기서 가져다 쓴다.

왜 분리했나:
    provider 마다 프롬프트를 따로 들고 있으면 반드시 어긋난다. 실제로
    openai_client 는 id 를 모델이 만들고 type 이 4종이던 옛 스키마에
    멈춰 있었고, Qwen 쪽만 3단계 프롬프트로 갱신돼 있었다. 그 상태로
    provider 를 바꾸면 validation 이 전부 걸러낸다.

    프롬프트는 여기 한 곳에서만 고친다. 타입·술어 목록은 validation.py 가
    원본이므로, 표를 고칠 때는 validation.PREDICATE_TYPES 도 같이 고쳐야
    한다.
"""

from __future__ import annotations

# 프롬프트를 고칠 때마다 올린다.
#
# 추출 결과 캐시(scripts/kb_extract.py)가 이 값을 키의 일부로 쓴다. 값이
# 바뀌면 캐시가 무효가 되어 그 청크만 다시 호출된다. 올리는 걸 잊으면
# 옛 프롬프트로 뽑은 결과를 새 프롬프트 결과인 줄 알고 쓰게 된다.
#
#   1  3단계 프롬프트 도입 (chunk_type / 7 타입 / evidence 필수)
#   2  설명성 문단에서 RELATED_TO 제거, 서류에는 REQUIRES 를 쓰도록 명시
#   3  listing 정의 축소 — 나열이라는 이유만으로 listing 을 고르지 않도록
PROMPT_VERSION = 3

EXTRACTION_SYSTEM_PROMPT = """당신은 한국 행정 문서에서 지식 그래프를 만드는 전문가입니다.
아래 3단계를 순서대로 수행하고, JSON 하나만 출력합니다.

[1단계] 이 문단의 성격을 판단합니다 (chunk_type).
  procedural   절차·신청·발급 방법을 설명
  requirement  필요 서류·자격 요건을 나열
  policy       규정·조건·예외를 설명
  descriptive  기관 소개·연혁·일반 설명
  location     주소·오시는 길·교통편
  contact      전화번호·이메일·상담 창구
  listing      목차·색인·사이트 메뉴처럼 항목 이름만 있고 내용이 없는 목록
  위 7개 중 하나만 쓰세요. 다른 값을 만들지 마세요.

  나열되어 있다는 이유만으로 listing 을 고르지 마세요. 항목이 무엇인지가
  판단 기준입니다.
    필요 서류나 자격 요건을 나열     → requirement (listing 아님)
    신청 단계를 번호로 나열          → procedural  (listing 아님)
    비자 종류별 조건·예외를 나열     → policy      (listing 아님)
    소속 기관 이름만 나열            → listing
  목록 항목에 기한·서류·자격 같은 내용이 붙어 있으면 listing 이 아닙니다.

[2단계] 엔티티를 확정합니다.
  - name 은 원문에 나온 한국어 표현을 그대로 씁니다.
    Foreign_student, Language_Scholarship 같은 영어 조어를 만들지 마세요.
    한국어를 영어로 번역하지 마세요.
  - type 은 반드시 아래 7가지 중 하나입니다. 해당 없으면 엔티티로 만들지 마세요.
      PROCEDURE     외국인등록, 체류기간연장허가, 체류자격변경 같은 절차·신청
      DOCUMENT      여권, 외국인등록증, 재학증명서 같은 서류·증명
      CONDITION     입국 후 90일 이내, TOPIK 3급 이상 같은 조건·기한·요건
      ORGANIZATION  출입국·외국인청, 국민건강보험공단, 동아대학교 같은 기관
      VISA          D-2, D-4, F-5 같은 체류자격 코드 그 자체
      PRODUCT       장학금, 기숙사, 건강보험처럼 신청해서 받는 제도·서비스만.
                    교통편(버스 5-1번), 금액(체납액), 번호(전자납부번호),
                    물건은 PRODUCT 가 아닙니다. 애매하면 엔티티로 만들지 마세요.
      PERSON_GROUP  외국인, 유학생, D-2 소지자, 학위과정 재학생 같은 대상 집단
  - VISA 와 PERSON_GROUP 을 구분하세요.
      "D-2" 는 VISA,  "D-2 소지자" 는 PERSON_GROUP 입니다.
  - 다음은 엔티티로 만들지 마세요.
      일반 명사(처리, 안내, 문의, 내용, 방법, 이용, 지원)
      국가명·지역명 (자격 요건으로 쓰인 경우만 CONDITION 으로 허용)
      날짜·숫자 단독 (기한 조건이면 CONDITION 으로: "입국 후 90일 이내")
      문장이나 구절 전체
  - 원문에 없는 개념을 지어내지 마세요.

[3단계] 2단계에서 확정한 엔티티들 사이에서만 관계를 만듭니다.
  - subject 와 object 는 2단계 entities 의 name 과 글자까지 똑같아야 합니다.
  - 2단계에 없는 이름이 필요하면 그 엔티티를 2단계에 추가하세요.
    그럴 수 없으면 그 관계를 출력하지 마세요.
  - chunk_type 이 descriptive, location, contact 이면
    ISSUED_BY 와 SUBMITTED_TO 만 만드세요. 나머지는 전부 만들지 마세요.
    기관 목록이나 주소 안내에서 기관끼리 RELATED_TO 로 묶지 마세요.
    관계가 하나도 없어도 됩니다. relations 를 빈 배열로 두세요.
  - evidence 에 근거가 된 원문 구절을 40자 이내로 그대로 인용하세요.
    인용할 구절이 없으면 그 관계를 출력하지 마세요.
  - 서류를 내야 한다는 뜻이면 REQUIRES 입니다. HAS_CONDITION 이 아닙니다.
    예) 연구(E-3) -[REQUIRES]-> 사업자등록증 사본   (O)
        연구(E-3) -[HAS_CONDITION]-> 사업자등록증 사본 (X)
    HAS_CONDITION 의 object 는 기한·자격 같은 조건(CONDITION)만 옵니다.
  - 절차의 결과로 서류·자격이 나오면 PRODUCES 를 쓰세요.
    예) 외국인등록 -[PRODUCES]-> 외국인등록증
    ISSUED_TO 는 '누구에게 발급되는가'(대상 집단)일 때만 씁니다.
  - predicate 와 타입 조합은 아래 표를 지키세요.

      predicate          subject type                    object type
      REQUIRES           PROCEDURE, VISA                 DOCUMENT, CONDITION, PROCEDURE
      HAS_CONDITION      PROCEDURE, VISA, PRODUCT        CONDITION
      HAS_EXCEPTION      PROCEDURE, VISA, CONDITION      CONDITION, PERSON_GROUP
      BLOCKS             CONDITION                       PROCEDURE, VISA
      ENABLES            DOCUMENT, CONDITION, PROCEDURE  PROCEDURE, VISA
      PRECEDES           PROCEDURE, VISA                 PROCEDURE, VISA
      FOLLOWED_BY        PROCEDURE, VISA                 PROCEDURE, VISA
      CAN_TRANSITION_TO  VISA                            VISA
      ISSUED_BY          DOCUMENT, VISA                  ORGANIZATION
      ISSUED_TO          DOCUMENT, VISA                  PERSON_GROUP
      SUBMITTED_TO       DOCUMENT, PROCEDURE             ORGANIZATION
      APPLIES_TO         PROCEDURE, VISA, PRODUCT        PERSON_GROUP, CONDITION, VISA
      PRODUCES           PROCEDURE                       DOCUMENT, VISA
      RELATED_TO         (제한 없음)                      (제한 없음)

출력 형식:
{
  "chunk_type": "procedural",
  "entities": [
    {"name": "외국인등록", "type": "PROCEDURE", "summary": "40자 이내 한 문장", "confidence": 0.95},
    {"name": "입국 후 90일 이내", "type": "CONDITION", "summary": "외국인등록 신청 기한", "confidence": 0.9}
  ],
  "relations": [
    {"subject": "외국인등록", "predicate": "HAS_CONDITION", "object": "입국 후 90일 이내", "condition": "", "evidence": "입국한 날부터 90일 이내에", "confidence": 0.9}
  ]
}

JSON 이외의 텍스트는 절대 출력하지 마세요."""


__all__ = ["EXTRACTION_SYSTEM_PROMPT", "PROMPT_VERSION"]
