# Git/GitHub 개발 환경 완성 가이드 (Windows, PowerShell)

아래 순서대로 실행하면 계정 확인 -> SSH 키 -> 테스트 저장소 연결 -> 첫 커밋/푸시까지 완료할 수 있다.

## 1) Git 기본 설정

```powershell
git --version
git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_EMAIL@example.com"
git config --global init.defaultBranch main
git config --global core.autocrlf true
```

확인:

```powershell
git config --global --list
```

## 2) GitHub CLI 로그인 (권장)

```powershell
gh --version
gh auth login
```

- GitHub.com 선택
- 프로토콜은 SSH 선택
- 브라우저 인증 완료

로그인 확인:

```powershell
gh auth status
```

## 3) SSH 키 생성/등록

```powershell
ssh-keygen -t ed25519 -C "YOUR_EMAIL@example.com"
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
ssh-add $HOME\.ssh\id_ed25519
Get-Content $HOME\.ssh\id_ed25519.pub
```

- 출력된 공개키를 GitHub > Settings > SSH and GPG keys > New SSH key에 등록

연결 테스트:

```powershell
ssh -T git@github.com
```

## 4) 테스트 저장소 생성 (원격)

```powershell
gh repo create YOUR_GITHUB_ID/git-test --private --confirm
git clone git@github.com:YOUR_GITHUB_ID/git-test.git
cd git-test
```

## 5) 첫 커밋/푸시

```powershell
"# Git Test" | Out-File -Encoding utf8 README.md
git add README.md
git commit -m "chore: initial commit"
git push -u origin main
```

## 6) 현재 yhs 저장소에서 첫 작업 커밋/푸시 예시

현재 저장소는 이미 원격이 연결되어 있으므로 아래처럼 진행 가능:

```powershell
cd C:\Users\DSL\OneDrive\문서\GitHub\yhs
git switch -c feat/semester-proposal

git add docs\semester_project_proposal.md docs\PRD_Campus_Navigator_RAG.md docs\git_github_setup_and_first_push.md docs\github_profile_README_template.md
git commit -m "docs: add semester proposal, PRD, and github setup guide"
git push -u origin feat/semester-proposal
```

## 7) 문제 해결 체크포인트

1. Permission denied (publickey)
- `ssh-add` 재실행, GitHub 등록 키 확인

2. author identity unknown
- `git config --global user.name/user.email` 재설정

3. push 거부(non-fast-forward)
- `git pull --rebase origin <branch>` 후 다시 push
