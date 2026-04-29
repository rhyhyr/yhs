# Wiki Publish Guide

이 디렉터리의 마크다운 문서는 GitHub Wiki에 올리기 위해 준비된 파일입니다.

- Home.md
- Getting Started.md
- Development Guide.md
- Troubleshooting.md

## 1) GitHub에서 Wiki 활성화하기

1. 저장소의 Settings로 이동합니다.
2. Features 항목을 찾습니다.
3. Wiki를 활성화합니다.

Wiki가 꺼져 있으면 `*.wiki.git` 클론 주소로 접근할 때 "Repository not found"가 나타납니다.

## 2) 페이지 발행하기

프로젝트 루트에서 아래 명령을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_wiki.ps1
```

## 3) 링크 확인하기

Wiki 탭을 열고 각 페이지 링크가 맞는지 확인합니다.

- Home -> Getting Started / Development Guide / Troubleshooting
- Getting Started -> Development Guide / Troubleshooting
- Development Guide -> Getting Started / Troubleshooting
- Troubleshooting -> Getting Started / Development Guide

## 참고

이 초안은 Wiki 문법과 일반 마크다운 링크를 같이 넣어 두었습니다.
저장소 미리보기와 GitHub Wiki 둘 다에서 문서 연결이 보이도록 하기 위한 구성입니다.
