<#
.SYNOPSIS
    yhs 개발·실행 명령 모음 (Windows).

.DESCRIPTION
    자주 쓰는 명령을 한 곳에 모아 둔 진입점입니다.
    실행되는 실제 명령을 매번 출력하므로, 익숙해지면 그대로 직접 쓰셔도 됩니다.

.EXAMPLE
    .\scripts\dev.ps1 help
    .\scripts\dev.ps1 up
    .\scripts\dev.ps1 logs backend
#>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help",

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Rest
)

$ErrorActionPreference = "Stop"

# 어디서 실행하든 저장소 루트를 기준으로 동작한다.
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$GpuCompose = @("-f", "docker-compose.yml", "-f", "deploy/docker-compose.gpu.yml")

function Write-Step($text) {
    Write-Host ""
    Write-Host "→ $text" -ForegroundColor Cyan
}

function Invoke-Step {
    <# 실행할 명령을 보여 주고 실행한다. 실패하면 즉시 중단. #>
    param([string]$Exe, [string[]]$Args)
    Write-Host "  $ $Exe $($Args -join ' ')" -ForegroundColor DarkGray
    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "명령이 실패했습니다 (exit $LASTEXITCODE): $Exe $($Args -join ' ')"
    }
}

function Require-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Host ""
        Write-Host ".env 파일이 없습니다. 템플릿을 복사합니다." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host ""
        Write-Host "  .env 를 열어 최소한 아래 값을 채운 뒤 다시 실행하세요:" -ForegroundColor Yellow
        Write-Host "    NEO4J_PASSWORD=..."
        Write-Host "    OPENAI_API_KEY=...   (RUNTIME_LLM=openai 로 쓸 때)"
        exit 1
    }
}

function Require-BackendInstalled {
    # backend/ 아래에서 import yhs 가 되는지 본다.
    # 안 되면 editable 설치가 아직 안 된 것이다.
    Push-Location "backend"
    try {
        & python -c "import yhs" 2>$null | Out-Null
        $ok = ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }

    if (-not $ok) {
        Write-Host ""
        Write-Host "  백엔드 패키지가 설치돼 있지 않습니다." -ForegroundColor Yellow
        Write-Host "    먼저 실행하세요:  .\scripts\dev.ps1 install"
        Write-Host "    (도커로만 쓸 거라면 이 명령 대신 .\scripts\dev.ps1 up 을 쓰세요)"
        exit 1
    }
}

function Get-EnvValue($name) {
    if (-not (Test-Path ".env")) { return $null }
    foreach ($line in Get-Content ".env" -Encoding UTF8) {
        if ($line -match "^\s*$name\s*=\s*(.*)$") { return $Matches[1].Trim() }
    }
    return $null
}

function Show-Help {
    Write-Host ""
    Write-Host "yhs 개발 명령" -ForegroundColor White
    Write-Host "  사용법: .\scripts\dev.ps1 <명령>"
    Write-Host ""
    Write-Host "  도커로 전체 실행" -ForegroundColor White
    Write-Host "    up             스택 기동 (CPU torch) — 처음이라면 이것부터"
    Write-Host "    up-gpu         스택 기동 (CUDA torch + GPU 할당, NVIDIA 필요)"
    Write-Host "    down           스택 정지·정리"
    Write-Host "    restart        스택 재기동"
    Write-Host "    build          이미지만 빌드"
    Write-Host "    logs [서비스]  로그 추적 (기본: backend)"
    Write-Host "    ps             컨테이너 상태"
    Write-Host ""
    Write-Host "  지식베이스" -ForegroundColor White
    Write-Host "    ingest         data/sources 의 PDF 를 Neo4j 에 적재 (LLM 호출·비용 발생)"
    Write-Host "    migrate-kb     다른 Neo4j 의 그래프를 컨테이너로 복사 (LLM 미사용)"
    Write-Host "    kb-status      적재 상태 확인 (노드·청크 수)"
    Write-Host ""
    Write-Host "  도커 없이 로컬 개발" -ForegroundColor White
    Write-Host "    install        백엔드·프론트 의존성 설치"
    Write-Host "    backend        백엔드 개발 서버 (http://localhost:8000)"
    Write-Host "    frontend       프론트 개발 서버 (http://localhost:5173)"
    Write-Host "    cli            터미널 질의 루프"
    Write-Host ""
    Write-Host "  품질" -ForegroundColor White
    Write-Host "    test           백엔드 단위 테스트"
    Write-Host "    lint           파이썬 + 프론트 린트"
    Write-Host "    fmt            자동 수정 가능한 린트 문제 고치기"
    Write-Host "    clean          캐시·빌드 산출물 정리"
    Write-Host ""
    Write-Host "  접속 주소" -ForegroundColor White
    Write-Host "    프론트  http://localhost:3000"
    Write-Host "    API 문서 http://localhost:8000/docs"
    Write-Host "    Neo4j   http://localhost:7474"
    Write-Host ""
}

switch ($Command.ToLower()) {

    "help" { Show-Help }

    "up" {
        Require-EnvFile
        Write-Step "도커 스택 기동 (CPU torch)"
        Invoke-Step "docker" @("compose", "up", "-d", "--build")
        Write-Host ""
        Write-Host "  기동했습니다. 백엔드는 임베딩 모델을 올리느라 1~3분 걸립니다." -ForegroundColor Green
        Write-Host "    상태 확인: .\scripts\dev.ps1 ps"
        Write-Host "    로그 보기: .\scripts\dev.ps1 logs"
        Write-Host "    프론트   : http://localhost:3000"
    }

    "up-gpu" {
        Require-EnvFile
        Write-Step "도커 스택 기동 (CUDA torch + GPU)"
        Write-Host "  GPU 가 도커에서 보이는지 먼저 확인하세요:" -ForegroundColor DarkGray
        Write-Host "    docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi" -ForegroundColor DarkGray
        Invoke-Step "docker" ($GpuCompose + @("up", "-d", "--build"))
        Write-Host ""
        Write-Host "  GPU 사용 여부는 백엔드 로그에서 확인합니다:" -ForegroundColor Green
        Write-Host "    임베딩 모델 로드 완료: BAAI/bge-m3 (device=cuda:0)"
    }

    "down" {
        Write-Step "도커 스택 정지"
        Invoke-Step "docker" @("compose", "down")
    }

    "restart" {
        Write-Step "도커 스택 재기동"
        Invoke-Step "docker" @("compose", "restart")
    }

    "build" {
        Write-Step "이미지 빌드"
        Invoke-Step "docker" @("compose", "build")
    }

    "logs" {
        $service = if ($Rest -and $Rest.Count -gt 0) { $Rest[0] } else { "backend" }
        Write-Step "$service 로그 (Ctrl+C 로 종료)"
        Invoke-Step "docker" @("compose", "logs", "-f", "--tail", "100", $service)
    }

    "ps" {
        Invoke-Step "docker" @("compose", "ps")
    }

    "ingest" {
        Write-Step "지식베이스 구축 (data/sources → Neo4j)"
        Write-Host "  PDF 마다 LLM 을 부르므로 시간과 API 비용이 듭니다." -ForegroundColor Yellow
        Invoke-Step "docker" @("compose", "exec", "backend", "yhs", "--ingest")
    }

    "migrate-kb" {
        Write-Step "다른 Neo4j 의 그래프를 컨테이너로 복사"
        $pw = Get-EnvValue "NEO4J_PASSWORD"
        if (-not $pw) { throw ".env 에 NEO4J_PASSWORD 가 없습니다." }
        $src = if ($Rest -and $Rest.Count -gt 0) { $Rest[0] } else { "neo4j://host.docker.internal:7687" }
        Write-Host "  원본: $src" -ForegroundColor DarkGray
        Write-Host "  대상: neo4j://neo4j:7687 (컨테이너)" -ForegroundColor DarkGray
        Get-Content "scripts/copy_graph.py" -Raw -Encoding UTF8 | docker compose exec -T `
            -e SRC_URI=$src -e SRC_USER=neo4j -e SRC_PASSWORD=$pw `
            -e DST_URI=neo4j://neo4j:7687 -e DST_USER=neo4j -e DST_PASSWORD=$pw `
            -e PYTHONIOENCODING=utf-8 `
            backend python -
        if ($LASTEXITCODE -ne 0) { throw "이관에 실패했습니다." }
    }

    "kb-status" {
        Write-Step "지식베이스 적재 상태"
        $pw = Get-EnvValue "NEO4J_PASSWORD"
        if (-not $pw) { throw ".env 에 NEO4J_PASSWORD 가 없습니다." }
        $cypher = "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC"
        Invoke-Step "docker" @("compose", "exec", "-T", "neo4j", "cypher-shell", "-u", "neo4j", "-p", $pw, $cypher)
    }

    "install" {
        Write-Step "백엔드 의존성 설치"
        Push-Location "backend"
        try {
            Invoke-Step "python" @("-m", "pip", "install", "-e", ".[dev]")
            Invoke-Step "python" @("-m", "playwright", "install", "chromium")
        } finally { Pop-Location }

        Write-Step "프론트 의존성 설치"
        Push-Location "frontend"
        try { Invoke-Step "npm" @("ci") } finally { Pop-Location }
    }

    "backend" {
        Require-BackendInstalled
        Write-Step "백엔드 개발 서버 (http://localhost:8000/docs)"
        Push-Location "backend"
        try { Invoke-Step "python" @("-m", "uvicorn", "yhs.api.main:app", "--reload") }
        finally { Pop-Location }
    }

    "frontend" {
        Write-Step "프론트 개발 서버 (http://localhost:5173)"
        Push-Location "frontend"
        try { Invoke-Step "npm" @("run", "dev") } finally { Pop-Location }
    }

    "cli" {
        Require-BackendInstalled
        Write-Step "터미널 질의 루프"
        Push-Location "backend"
        try { Invoke-Step "python" @("-m", "yhs.cli", "--query") } finally { Pop-Location }
    }

    "test" {
        Write-Step "백엔드 단위 테스트 (integration 제외)"
        Push-Location "backend"
        try { Invoke-Step "python" @("-m", "pytest", "-m", "not integration") }
        finally { Pop-Location }
    }

    "lint" {
        Write-Step "파이썬 린트 (ruff)"
        Invoke-Step "python" @("-m", "ruff", "check", ".")
        Write-Step "프론트 린트 (eslint)"
        Push-Location "frontend"
        try { Invoke-Step "npm" @("run", "lint") } finally { Pop-Location }
    }

    "fmt" {
        Write-Step "자동 수정 (ruff --fix)"
        Invoke-Step "python" @("-m", "ruff", "check", "--fix", ".")
    }

    "clean" {
        Write-Step "캐시·빌드 산출물 정리"
        $targets = @(".cache", ".ruff_cache", ".pytest_cache", "backend/coverage.xml", "frontend/dist")
        foreach ($t in $targets) {
            if (Test-Path $t) { Remove-Item -Recurse -Force $t; Write-Host "  삭제: $t" }
        }
        Get-ChildItem -Path . -Include "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch "node_modules|\.venv" } |
            ForEach-Object { Remove-Item -Recurse -Force $_.FullName; Write-Host "  삭제: $($_.FullName)" }
        Write-Host "  정리 완료" -ForegroundColor Green
    }

    default {
        Write-Host ""
        Write-Host "알 수 없는 명령: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
