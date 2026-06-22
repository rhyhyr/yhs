# YHS — 문서 작성 채널 개발 문서

> RAG 기반 유학생 맞춤형 생활·행정 AI 어시스턴트 (YHS)  
> 기존 파이프라인에 **문서 작성 채널(document_filling)** 을 통합하는 작업

---

## 팀 구성 & 담당

| 이름 | 역할 | 담당 |
|------|------|------|
| 류화영 | 팀장/PM | API 연동 및 상태 관리 |
| 김수미 | BE | 크롤링 파이프라인 설계 |
| 박소현 | FE | UI/UX 설계 및 화면 구현 |
| 윤태이 | BE | DB 구축, 파이프라인 설계 |

---

## 기존 YHS 아키텍처 요약

```
유학생 질문 (다국어)
        ↓
다국어 처리 + 엔티티 추출
  └─ variable_dictionary (200개+ 용어 매핑)
        ↓
점수 계산: 벡터유사도 × 0.6 + 키워드점수 × 0.4
        ↓
┌─────────────────────────────────────┐
│ Fast Path  score ≥ 0.17, 청크 ≥ 2  │ → 단순 질문
│ Deep Path  범위 확장 탐색            │ → 복합 질문
│ Crawling   Playwright (최후 수단)    │ → 미탐색 정보
└─────────────────────────────────────┘
        ↓
Neo4j Knowledge Graph 탐색
        ↓
Gemini 2.5 Flash → 최종 답변 (채널 단위)
```

---

## 문서 작성 채널이란

기존 채널 (비자&체류, 취업&아르바이트 등)과 동일한 구조의 **새 채널 타입**.

```
사용자: "휴학신청서 작성하고 싶어"
  → 의도 파악: document_filling 채널 생성
  → 문서 업로드 요청
  → 필드 인식 + 개인정보 자동 채우기
  → 나머지 필드 중국어 질문 (variable_dictionary 재활용)
  → Gemini로 한국어 공식 문체 재작성
  → DOCX 채우기 + 반환
```

기존 파이프라인과 달리 **답변 텍스트가 아닌 완성된 DOCX 파일**이 output.

---

## 통합 지점

| 기존 컴포넌트 | 문서 채널에서 활용 방식 |
|--------------|------------------------|
| variable_dictionary | 중국어 질문 생성 시 행정 용어 매핑에 재활용 |
| Gemini 2.5 Flash | 필드 인식 + 한국어 공식 문체 재작성 |
| 채널 단위 구조 | document_filling을 새 채널 타입으로 추가 |
| 세션 상태 관리 | 필드 JSON 상태를 기존 세션 구조에 추가 |
| 다국어 처리 | 중국어 입력 → 기존 파이프라인 그대로 통과 |

---

## 데이터 모델 추가

### 기존 세션에 추가되는 document 상태

```json
{
  "session_id": "uuid",
  "channel_type": "document_filling",
  "user_id": "uuid",
  "document": {
    "original_filename": "휴학신청서.docx",
    "stored_path": "/storage/docs/uuid.docx",
    "fields": {
      "field_1": {
        "label_ko": "성명",
        "value_zh": "张伟",
        "value_ko": "장웨이",
        "status": "auto_filled"
      },
      "field_2": {
        "label_ko": "휴학 사유",
        "value_zh": "因家庭经济困难",
        "value_ko": "가계 경제 사정 악화로 인하여 학업을 지속하기 어려운 상황입니다.",
        "status": "filled"
      },
      "field_3": {
        "label_ko": "지도교수",
        "value_zh": null,
        "value_ko": null,
        "status": "skipped"
      }
    },
    "output_path": "/storage/output/uuid_filled.docx"
  }
}
```

### 사용자 프로필 (회원가입 시 수집)

```json
{
  "user_id": "uuid",
  "name_ko": "장웨이",
  "name_zh": "张伟",
  "student_id": "20241234",
  "department": "컴퓨터공학과",
  "nationality": "CN",
  "visa_type": "D-2"
}
```

---

## Step-by-Step 구현

---

### Step 1 — 채널 의도 파악 확장

기존 의도 분류기에 `document_filling` 카테고리 추가.

**추가할 트리거 패턴 (variable_dictionary에 등록)**

```
ZH: 申请书, 申请表, 文件, 材料, 填写, 表格
KO: 신청서, 서류, 양식, 작성, 서식
EN: application form, document, fill out
```

**의도 분류 로직 수정**

```python
DOCUMENT_KEYWORDS = ["신청서", "서류", "양식", "작성", "申请书", "填写"]

def classify_intent(query: str, entities: list) -> str:
    # 기존 Fast/Deep Path 분류 로직 유지
    # document_filling 체크를 먼저 수행
    if any(kw in query for kw in DOCUMENT_KEYWORDS):
        return "document_filling"
    
    # 기존 로직 실행
    score = calculate_score(entities)
    if score >= 0.17:
        return "fast_path"
    ...
```

---

### Step 2 — DOCX 파싱 모듈 (신규)

```bash
pip install python-docx
```

```python
from docx import Document

def extract_docx_content(file_path: str) -> dict:
    """
    DOCX에서 텍스트와 테이블을 추출
    한국 공문서는 대부분 표 기반 → 테이블 파싱 필수
    """
    doc = Document(file_path)
    content = {
        "paragraphs": [],
        "tables": []
    }
    
    for para in doc.paragraphs:
        if para.text.strip():
            content["paragraphs"].append(para.text)
    
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        content["tables"].append(table_data)
    
    return content
```

---

### Step 3 — Gemini 필드 인식

기존 Gemini 호출 구조에 필드 인식 프롬프트 추가.

```python
FIELD_DETECTION_PROMPT = """
다음은 한국 대학교 행정 서류의 내용입니다.
빈칸(___, 빈 셀, 괄호 등)으로 표시된 입력 필드를 찾아 JSON으로 반환하세요.

출력 형식:
{
  "fields": [
    {
      "field_id": "field_1",
      "label_ko": "성명",
      "field_type": "text",
      "is_personal_info": true,
      "location": "table_0_row_1_col_1"
    }
  ]
}

서류 내용:
{content}
"""
```

**is_personal_info 매핑 (기존 사용자 프로필 활용)**

```python
PERSONAL_INFO_LABELS = {
    "성명": "name_ko",
    "이름": "name_ko",
    "학번": "student_id",
    "학과": "department",
    "소속": "department",
    "국적": "nationality",
    "비자": "visa_type",
}

def autofill_from_profile(fields: list, user_profile: dict) -> dict:
    filled = {}
    for field in fields:
        if not field["is_personal_info"]:
            continue
        for label, attr in PERSONAL_INFO_LABELS.items():
            if label in field["label_ko"]:
                filled[field["field_id"]] = {
                    "value_ko": user_profile.get(attr),
                    "status": "auto_filled"
                }
    return filled
```

---

### Step 4 — 중국어 질문 생성 (variable_dictionary 재활용)

자동 채우기 안 된 필드에 대해 중국어 질문 생성.  
기존 `variable_dictionary`의 행정 용어 매핑을 역방향으로 활용.

```python
def get_zh_term(label_ko: str, var_dict: dict) -> str:
    """
    variable_dictionary에서 한국어 라벨의 중국어 표현 조회
    없으면 Gemini로 번역 후 신규 추가
    """
    for term_ko, mappings in var_dict.items():
        if term_ko in label_ko and "ZH" in mappings:
            return mappings["ZH"][0]
    
    # 미등록 용어 → Gemini 번역 → dictionary에 추가
    zh_term = gemini_translate(label_ko, target_lang="ZH")
    var_dict[label_ko] = {"ZH": [zh_term], "KO": [label_ko]}
    return zh_term


QUESTION_TEMPLATE = """
请问您的{zh_label}是什么？
（{explanation}）
"""

FIELD_EXPLANATIONS = {
    "휴학 사유": "请说明您需要休学的原因",
    "복학 예정일": "预计返校继续学业的日期",
    "지도교수": "您的指导教授/论文导师姓名",
}
```

---

### Step 5 — 한국어 공식 문체 재작성

기존 Gemini 호출에 재작성 프롬프트 추가.

```python
REWRITE_PROMPT = """
아래 내용을 한국 대학교 행정 서류 제출용 공식 문체로 재작성하세요.

규칙:
- 합니다/입니다 체 사용
- 감정 표현 배제, 객관적 서술
- 1~3문장으로 간결하게

원문 (중국어): {zh_text}
"""
```

**입력 → 출력 예시**
```
입력: 因为家里经济有点困难，父亲的生意不太好
출력: 부친의 사업 부진으로 가계 수입이 감소하여 경제적 어려움을 겪고 있습니다.
```

---

### Step 6 — DOCX 채우기

```python
from docx import Document
import re

def fill_docx(template_path: str, field_map: dict, output_path: str):
    """
    field_map: { "location": "value_ko" } 형태
    location은 Step 3에서 Gemini가 감지한 위치 정보 활용
    """
    doc = Document(template_path)
    
    # 단락 내 빈칸 패턴 교체
    for para in doc.paragraphs:
        for run in para.runs:
            for location, value in field_map.items():
                # ___ 패턴
                run.text = re.sub(r'_{2,}', value or '', run.text, count=1)
                # (  ) 패턴
                run.text = re.sub(r'\(\s*\)', f'({value or ""})', run.text, count=1)
    
    # 테이블 빈 셀 채우기
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_key = f"table_{doc.tables.index(table)}"
                if cell_key in field_map and not cell.text.strip():
                    cell.text = field_map[cell_key] or ''
    
    doc.save(output_path)
```

> ⚠️ **주의**: 원본 DOCX의 빈칸 패턴이 양식마다 다름. 실제 동아대 서류를 받아서 패턴 테스트 필수. `___`, 빈 셀, `( )` 중 어떤 방식인지 확인 후 정규식 조정 필요.

---

### Step 7 — 필드 대조표 생성 (확인용 출력)

```python
def generate_comparison_table(fields: dict) -> str:
    """
    중국어 입력값 ↔ 한국어 출력값 대조표 생성
    사용자가 내용 검토할 수 있도록 중국어로 반환
    """
    lines = ["请确认以下填写内容：\n확인해주세요：\n"]
    
    for field_id, field in fields.items():
        label = field["label_ko"]
        zh_val = field.get("value_zh") or "（跳过/미입력）"
        ko_val = field.get("value_ko") or "（空白/빈칸）"
        status_mark = "✓" if field["status"] != "skipped" else "—"
        
        lines.append(f"{status_mark} {label}: {zh_val} → {ko_val}")
    
    return "\n".join(lines)
```

---

### Step 8 — 수정 루프

사용자가 "3번 항목 바꿔줘" 요청 시 해당 필드만 업데이트.

```python
EDIT_INTENT_PROMPT = """
사용자 요청: "{user_message}"

현재 필드 목록:
{fields_json}

수정하려는 field_id와 이유를 추출하세요.
출력: {"field_id": "field_2", "reason": "내용 변경 요청"}
"""

def handle_edit_request(user_message: str, session: dict) -> str:
    # 1. Gemini로 수정 대상 field_id 추출
    target = gemini_extract_edit_intent(user_message, session["fields"])
    
    # 2. 해당 필드만 재질문
    field = session["fields"][target["field_id"]]
    zh_label = get_zh_term(field["label_ko"])
    return f"请重新描述一下{zh_label}的内容："

    # 3. 새 답변 수신 → Step 5 재실행 → DOCX 재생성
```

---

## 신규 API 엔드포인트

기존 API에 추가되는 엔드포인트만 기술.

```
POST   /channels/document/create        # 문서 채널 생성
POST   /channels/document/upload        # DOCX 업로드
GET    /channels/{id}/next-question     # 다음 질문 (기존 채널 구조 재활용)
POST   /channels/{id}/answer            # 답변 제출
POST   /channels/{id}/skip              # 필드 스킵
POST   /channels/{id}/edit              # 특정 필드 수정
GET    /channels/{id}/document/download # 완성 DOCX 다운로드
```

---

## 구현 순서 (윤태이 담당 위주)

| 순서 | 내용 | 비고 |
|------|------|------|
| 1 | 동아대 DOCX 양식 수집 + 빈칸 패턴 분석 | **먼저 해야 함** |
| 2 | DOCX 파싱 모듈 (Step 2) | python-docx |
| 3 | Gemini 필드 인식 프롬프트 (Step 3) | 기존 Gemini 호출 구조에 추가 |
| 4 | 개인정보 자동 채우기 (Step 3) | 사용자 프로필 스키마 정의 |
| 5 | variable_dictionary 역방향 조회 (Step 4) | 기존 DB 재활용 |
| 6 | 한국어 재작성 프롬프트 (Step 5) | 기존 Gemini 호출에 추가 |
| 7 | DOCX 채우기 + 저장 (Step 6) | 패턴 확인 후 정규식 조정 |
| 8 | 대조표 생성 (Step 7) | |
| 9 | 수정 루프 (Step 8) | |
| 10 | 박소현 FE와 API 연동 테스트 | 류화영 상태 관리 연동 |

---

## 미결 사항

- [ ] 동아대 DOCX 실제 양식 수집 → 빈칸 패턴 확인 (최우선)
- [ ] 세션 상태에 document 필드 추가 (기존 세션 스키마 수정)
- [ ] 파일 저장 위치 결정 (로컬 vs S3 등)
- [ ] 채널 의도 분류 임계값 조정 (document 키워드 추가 후 재검증)
