"""
scripts/collect_urls.py
URL 목록을 웹에서 가져와 텍스트 정제 후 PDF로 변환, data/sources/ 에 저장한다.
사용법: python scripts/collect_urls.py
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

# ── 폰트 등록 ─────────────────────────────────────────────────────────────────
# 한글 PDF 를 만들려면 한글 글리프를 가진 TTF 가 필요하다.
# OS 마다 경로가 달라서 후보를 순서대로 찾고, 하나도 없으면 reportlab 이
# 내장한 CID 폰트(HeiseiKakuGo-W5)로 떨어진다 — 모양은 덜 예쁘지만 깨지진 않는다.
_FONT_CANDIDATES = [
    # Windows
    ("Malgun", "MalgunBd", Path("C:/Windows/Fonts/malgun.ttf"), Path("C:/Windows/Fonts/malgunbd.ttf")),
    # macOS
    ("AppleGothic", "AppleGothic", Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"), None),
    # Linux (fonts-nanum / fonts-noto-cjk)
    ("NanumGothic", "NanumGothicBold",
     Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
     Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf")),
    ("NotoSansKR", "NotoSansKR",
     Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), None),
]


def _register_korean_font() -> tuple[str, str]:
    """사용 가능한 한글 폰트를 등록하고 (본문, 볼드) 폰트명을 돌려준다."""
    for regular, bold, reg_path, bold_path in _FONT_CANDIDATES:
        if not reg_path.is_file():
            continue
        pdfmetrics.registerFont(TTFont(regular, str(reg_path)))
        if bold_path and bold_path.is_file():
            pdfmetrics.registerFont(TTFont(bold, str(bold_path)))
            return regular, bold
        return regular, regular

    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    print(
        "[경고] 한글 TTF 를 찾지 못해 내장 CID 폰트로 대체합니다.",
        "Linux 라면: sudo apt install fonts-nanum",
        sep="\n",
        file=sys.stderr,
    )
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    return "HeiseiKakuGo-W5", "HeiseiKakuGo-W5"


FONT_REGULAR, FONT_BOLD = _register_korean_font()

# ── 경로 ──────────────────────────────────────────────────────────────────────
# 인제스트 대상 코퍼스와 같은 위치에 떨군다 (backend 의 PDF_DIR 기본값).
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sources"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# ── 수집 대상 ──────────────────────────────────────────────────────────────────
TARGETS = [
    # (파일번호, 파일명_스템, 자료명, 출처기관, URL)
    ("10", "하이코리아_외국인등록증_재발급",
     "외국인등록증 발급/재발급/교부",
     "법무부 하이코리아",
     "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=178&PARENT_ID=139"),

    ("11", "하이코리아_외국인등록사항_변경신고",
     "외국인등록사항 변경신고",
     "법무부 하이코리아",
     "https://www.hikorea.go.kr/info/InfoDatail.pt?CAT_SEQ=180&PARENT_ID=139"),

    ("12", "하이코리아_체류기간연장허가",
     "등록외국인 체류기간연장허가(전자민원)",
     "법무부 하이코리아",
     "https://www.hikorea.go.kr/cvlappl/cvlapplInfoR.pt?CAT_SEQ=1808"),

    ("13", "하이코리아_전자민원목록",
     "하이코리아 전자민원 목록",
     "법무부 하이코리아",
     "https://www.hikorea.go.kr/cvlappl/CvlapplStep1.pt"),

    ("14", "비자포털_절차",
     "대한민국 비자포털 비자 절차",
     "법무부 대한민국 비자포털",
     "https://www.visa.go.kr/openPage.do?MENU_ID=10105"),

    ("15", "출입국_1345_외국인종합안내센터",
     "1345 외국인종합안내센터",
     "법무부 출입국·외국인정책본부",
     "https://www.immigration.go.kr/immigration/1530/subview.do"),

    ("16", "출입국_부산청_기관소개",
     "부산출입국·외국인청 기관소개",
     "법무부 출입국·외국인정책본부",
     "https://www.immigration.go.kr/immigration/1678/subview.do"),

    ("17", "출입국_부산청_오시는길",
     "부산출입국·외국인청 오시는 길",
     "법무부 출입국·외국인정책본부",
     "https://www.immigration.go.kr/immigration/1619/subview.do"),

    ("18", "출입국_부산경남_소속기관",
     "부산/경남 소속기관 목록",
     "법무부 출입국·외국인정책본부",
     "https://www.immigration.go.kr/immigration/2058/subview.do"),

    ("19", "NHIS_건강보험_적용기준_고시",
     "장기체류 재외국민 및 외국인에 대한 건강보험 적용기준 고시",
     "국민건강보험공단/보건복지부",
     "https://www.nhis.or.kr/lm/lmxsrv/law/lawFullContent.do?SEQ=41&SEQ_HISTORY=595302"),

    ("20", "동아대_국제교류과_보험안내",
     "동아대학교 국제교류과 보험 안내",
     "동아대학교 대외국제처 국제교류과",
     "https://rfc.donga.ac.kr/global/CMS/Contents/Contents.do?mCode=MN063"),

    ("21", "정부24_시간제취업",
     "정부24 외국인서비스 시간제취업",
     "행정안전부 정부24 외국인서비스",
     "https://foreigner.gov.kr/contents/foreignerContents/?htmlNo=m020103"),

    ("22", "동아대_휴학",
     "동아대학교 휴학 안내",
     "동아대학교",
     "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN124"),

    ("23", "동아대_복학",
     "동아대학교 복학 안내",
     "동아대학교",
     "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN125"),

    ("24", "동아대_수강신청_2026_1",
     "2026학년도 1학기 수강신청 안내",
     "동아대학교",
     "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN316"),

    ("25", "동아대_등록안내_2026_1",
     "2026학년도 1학기 재학생·복학생 등록 안내",
     "동아대학교",
     "https://www.donga.ac.kr/kor/CMS/Contents/Contents.do?mCode=MN318"),

    ("26", "동아대_장학금_학부_한국어트랙",
     "학부 한국어트랙 장학금",
     "동아대학교 국제교류과",
     "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN112"),

    ("27", "동아대_장학금_학부_영어트랙",
     "학부 영어트랙 장학금",
     "동아대학교 국제교류과",
     "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN077"),

    ("28", "동아대_장학금_대학원_한국어트랙",
     "대학원 한국어트랙 장학금",
     "동아대학교 국제교류과",
     "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN109"),

    ("29", "동아대_장학금_대학원_영어트랙",
     "대학원 영어트랙 장학금",
     "동아대학교 국제교류과",
     "https://dongaoia.donga.ac.kr/dongaoia/CMS/Contents/Contents.do?mCode=MN110"),

    ("30", "동아대_석당글로벌하우스",
     "동아대학교 석당 글로벌하우스",
     "동아대학교 석당 글로벌하우스",
     "http://globalhouse.donga.ac.kr"),

    ("31", "동아대_한림생활관",
     "동아대학교 한림생활관",
     "동아대학교 한림생활관",
     "https://hanlim.donga.ac.kr"),

    ("32", "금융위_모바일외국인등록증_계좌개설",
     "모바일 외국인등록증으로 계좌개설 가능 보도자료",
     "금융위원회·법무부·행정안전부",
     "https://www.fsc.go.kr/edu/news/84342"),

    ("33", "모바일신분증_외국인등록증_발급안내",
     "모바일 외국인등록증 발급안내",
     "행정안전부 모바일 신분증",
     "https://www.mobileid.go.kr/mip/hps/issuReqstGuidance/issuReqstGuidanceMfc.do"),

    ("34", "서울외국인포털_금감원_금융생활가이드북",
     "외국인을 위한 금융생활 가이드북 안내",
     "서울외국인포털/금융감독원",
     "https://global.seoul.go.kr/web/news/senw/bordContDetail.do?brd_no=5&lang=ko&mode=W&post_no=27DCB957CB550112E063C0A8A0236043"),

    ("35", "부산시_외국인주민지원",
     "부산광역시 외국인주민지원",
     "부산광역시",
     "https://www.busan.go.kr/depart/family0407"),

    ("36", "부산_외국인근로자지원센터_영문",
     "부산 Support Center for Foreign Workers",
     "부산광역시 영문",
     "https://www.busan.go.kr/eng/busan-support-center-for-foreign-workers"),

    ("37", "부산외국인근로자지원센터_콜센터",
     "부산 외국인 통합콜센터 안내",
     "부산외국인근로자지원센터",
     "https://bscfw.or.kr/notice_01.html?bid=167&botype=LIS_B02_03&page=1&page_num=10&query=view&table=LimBo"),
]


# ── 정제 함수 ─────────────────────────────────────────────────────────────────

REMOVE_TAGS = {
    "script", "style", "noscript", "nav", "header", "footer",
    "aside", "iframe", "form", "button", "input", "select",
    "meta", "link", "head",
}

SKIP_PATTERNS = re.compile(
    r"(로그인|회원가입|메뉴|검색|바로가기|sns|공유|프린트|top\s*으로|"
    r"관련\s*사이트|사이트맵|copyright|all\s*rights|모바일\s*버전)",
    re.I,
)


def extract_main_text(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(REMOVE_TAGS):
        tag.decompose()

    # 본문 영역 우선 탐색
    main = (
        soup.find("div", {"id": re.compile(r"content|main|article|body", re.I)})
        or soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|main|article", re.I))
        or soup.body
        or soup
    )

    lines: list[str] = []
    from bs4 import Tag
    for elem in main.descendants:
        if not isinstance(elem, Tag):
            continue
        tag = elem.name.lower() if elem.name else ""
        if not tag:
            continue

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = elem.get_text(" ", strip=True)
            if text:
                level = int(tag[1])
                prefix = "■" if level <= 2 else "▶" if level == 3 else "·"
                lines.append(f"\n{prefix} {text}\n")

        elif tag in ("p", "li", "dt", "dd", "td", "th"):
            text = elem.get_text(" ", strip=True)
            if text and len(text) > 3:
                if not SKIP_PATTERNS.search(text):
                    if tag in ("td", "th"):
                        lines.append(f"  {text}")
                    elif tag == "li":
                        lines.append(f"  • {text}")
                    else:
                        lines.append(text)

        elif tag == "tr":
            cells = [
                td.get_text(" ", strip=True)
                for td in elem.find_all(["th", "td"])
                if td.get_text(strip=True)
            ]
            if cells:
                lines.append("  " + " | ".join(cells))

        elif tag == "img":
            alt = elem.get("alt", "").strip()
            if alt and len(alt) > 3:
                lines.append(f"[이미지: {alt}]")

    # 중복 제거
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        key = line.strip()
        if key and key not in seen:
            seen.add(key)
            result.append(line)

    return "\n".join(result).strip()


# ── PDF 생성 ──────────────────────────────────────────────────────────────────

def make_pdf(filepath: Path, title: str, institution: str, url: str, body: str) -> None:
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1", fontName=FONT_BOLD, fontSize=14, leading=20, spaceAfter=6,
    )
    meta = ParagraphStyle(
        "Meta", fontName=FONT_REGULAR, fontSize=9, leading=13, textColor="#555555", spaceAfter=10,
    )
    body_style = ParagraphStyle(
        "Body", fontName=FONT_REGULAR, fontSize=10, leading=16, spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "H2", fontName=FONT_BOLD, fontSize=11, leading=16, spaceBefore=8, spaceAfter=4,
    )

    def safe(text: str) -> str:
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )

    story = [
        Paragraph(safe(title), h1),
        Paragraph(
            f"출처기관: {safe(institution)}<br/>"
            f"URL: {safe(url)}<br/>"
            f"수집일: 2026-06-17",
            meta,
        ),
        Spacer(1, 4 * mm),
    ]

    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 2 * mm))
            continue
        if stripped.startswith(("■", "▶")):
            story.append(Paragraph(safe(stripped), h2_style))
        elif stripped.startswith("·"):
            story.append(Paragraph(safe(stripped), h2_style))
        else:
            story.append(Paragraph(safe(stripped), body_style))

    doc.build(story)


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ok: list[str] = []
    fail: list[tuple[str, str]] = []

    for num, stem, title, institution, url in TARGETS:
        out_path = OUT_DIR / f"{num}_{stem}.pdf"
        if out_path.exists():
            print(f"[SKIP] {out_path.name} 이미 존재")
            ok.append(f"{num} {title}")
            continue

        print(f"[FETCH] {num} {title} ...", end=" ", flush=True)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            body = extract_main_text(resp.text, url)

            if len(body) < 100:
                raise ValueError(f"본문 너무 짧음 ({len(body)}자)")

            make_pdf(out_path, title, institution, url, body)
            print(f"OK ({len(body)}자)")
            ok.append(f"{num} {title}")

        except Exception as exc:
            print(f"FAIL → {exc}")
            fail.append((f"{num} {title}", str(exc)))

        time.sleep(0.5)

    print(f"\n=== 완료: 성공 {len(ok)}개, 실패 {len(fail)}개 ===")
    for name, err in fail:
        print(f"  FAIL: {name} -- {err}")


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    # Windows 콘솔 유니코드 출력
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
