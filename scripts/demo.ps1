# ─────────────────────────────────────────────────────────────────────────────
# 시연용 공개 링크 만들기.
#
# scripts\demo.bat 을 더블클릭하면 이 파일이 실행된다.
# 도커 스택을 올리고 → 준비를 기다리고 → 공개 링크를 만들어 클립보드에 넣는다.
#
# 한글이 들어가므로 반드시 PowerShell 로 둔다. .bat 안에 한글을 넣으면
# cmd 가 파일을 cp949 로 읽어 줄이 깨지고 엉뚱한 명령으로 해석된다.
# ─────────────────────────────────────────────────────────────────────────────

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$compose = @('-f', 'docker-compose.yml', '-f', 'deploy/docker-compose.prod.yml')
$log = Join-Path $env:TEMP 'yhs-tunnel.log'
$cf = 'C:\Program Files (x86)\cloudflared\cloudflared.exe'
if (-not (Test-Path $cf)) { $cf = 'cloudflared' }

function Fail($msg) {
    Write-Host ''
    Write-Host "  [실패] $msg" -ForegroundColor Red
    Write-Host ''
    Read-Host '  엔터를 누르면 창을 닫습니다'
    exit 1
}

function Test-DockerUp {
    docker version --format '{{.Server.Version}}' *> $null
    return $LASTEXITCODE -eq 0
}

Write-Host ''
Write-Host '  [1/4] 도커 확인'
if (-not (Test-DockerUp)) {
    Write-Host '        꺼져 있어 켜는 중... 최초 1~2분 걸립니다.'
    Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    $deadline = (Get-Date).AddMinutes(3)
    while (-not (Test-DockerUp)) {
        if ((Get-Date) -gt $deadline) { Fail '3분 기다렸는데 도커가 안 켜집니다. 직접 켜고 다시 실행하세요.' }
        Start-Sleep 5
    }
}
Write-Host '        준비됨'

Write-Host '  [2/4] 스택 기동'
docker compose @compose up -d
if ($LASTEXITCODE -ne 0) { Fail '스택을 못 올렸습니다. 위 오류를 확인하세요.' }

Write-Host '  [3/4] 백엔드 준비 대기 (임베딩 모델 로딩, 최대 3분)'
$deadline = (Get-Date).AddMinutes(3)
while ($true) {
    try {
        if ((Invoke-WebRequest 'http://localhost/health' -TimeoutSec 5 -UseBasicParsing).StatusCode -eq 200) { break }
    } catch { }
    if ((Get-Date) -gt $deadline) { Fail '백엔드가 응답하지 않습니다. 확인: docker compose logs backend --tail 50' }
    Start-Sleep 3
}
Write-Host '        준비됨'

Write-Host '  [4/4] 공개 링크 생성'
Remove-Item $log -ErrorAction SilentlyContinue
$tunnel = Start-Process -PassThru -WindowStyle Minimized -FilePath $cf `
    -ArgumentList 'tunnel', '--url', 'http://localhost:80', '--logfile', $log

$url = $null
$deadline = (Get-Date).AddSeconds(60)
while (-not $url) {
    if ((Get-Date) -gt $deadline) {
        Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
        Fail "60초 안에 링크가 안 나왔습니다. 로그를 보세요: $log"
    }
    Start-Sleep 1
    if (Test-Path $log) {
        $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -AllMatches
        if ($m) { $url = @($m.Matches.Value)[0] }
    }
}

try { Set-Clipboard $url } catch { }

Write-Host ''
Write-Host '  ==========================================================='
Write-Host ''
Write-Host "     $url" -ForegroundColor Green
Write-Host ''
Write-Host '     (클립보드에 복사됐습니다. 그대로 붙여넣어 공유하세요)'
Write-Host ''
Write-Host '  ==========================================================='
Write-Host ''
Write-Host '  * 이 창을 닫으면 링크가 죽습니다. 시연 끝날 때까지 켜두세요.'
Write-Host '  * 질문 1건당 약 10원이 OpenAI 로 과금됩니다.'
Write-Host ''

Start-Process $url
Read-Host '  엔터를 누르면 링크를 닫습니다'

Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
Write-Host '  링크를 닫았습니다. (도커 스택은 계속 돌고 있습니다)'
Start-Sleep 2
