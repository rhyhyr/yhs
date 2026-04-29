param(
    [string]$WikiRepoUrl = "https://github.com/nadasoom2/yhs_AIOSS.wiki.git",
    [string]$SourceDir = "wiki-drafts",
    [string]$WorkDir = "..\\yhs_AIOSS.wiki"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$sourcePath = Join-Path $repoRoot $SourceDir
if (-not (Test-Path $sourcePath)) {
    throw "Source directory not found: $sourcePath"
}

$wikiPath = Resolve-Path (Join-Path $repoRoot $WorkDir) -ErrorAction SilentlyContinue
if ($null -eq $wikiPath) {
    git clone $WikiRepoUrl $WorkDir
    $wikiPath = Resolve-Path (Join-Path $repoRoot $WorkDir)
}

Set-Location $wikiPath
git pull

Get-ChildItem -Path $sourcePath -File -Filter "*.md" | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $wikiPath $_.Name) -Force
}

git add *.md

$status = git status --porcelain
if (-not $status) {
    Write-Host "No wiki changes to commit."
    exit 0
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "docs(wiki): update wiki pages ($timestamp)"
git push

Write-Host "Wiki pages published successfully."
