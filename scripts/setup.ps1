<#
GKMKB teammate setup for Windows 10/11.
Run from the repo root in PowerShell:   .\scripts\setup.ps1
Add -Yes to skip install prompts.  Add -SkipDocker to skip Docker Desktop.
Safe to re-run. It installs only what is missing.
#>
param([switch]$Yes, [switch]$SkipDocker)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Refresh-Path {
  $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
  $u = [Environment]::GetEnvironmentVariable("Path", "User")
  $env:Path = "$m;$u"
}

function Has($cmd) { return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Ensure($label, $cmd, $wingetId) {
  if (Has $cmd) { Write-Host "[ok]   $label"; return }
  if (-not (Has "winget")) { throw "$label missing and winget not found. Install $label by hand, then re-run." }
  if (-not $Yes) {
    $a = Read-Host "$label missing. Install with winget? (y/n)"
    if ($a -ne "y") { throw "$label is required." }
  }
  Write-Host "[inst] $label"
  winget install --id $wingetId -e --accept-package-agreements --accept-source-agreements
  Refresh-Path
  if (-not (Has $cmd)) { Write-Host "[warn] $label installed but '$cmd' not on PATH yet. Open a new terminal and re-run." }
}

Write-Host "== GKMKB setup =="
Ensure "Git"        "git"    "Git.Git"
Ensure "Python 3.12" "python" "Python.Python.3.12"
Ensure "Node.js LTS" "node"   "OpenJS.NodeJS.LTS"
Ensure "GitHub CLI" "gh"     "GitHub.cli"
if (-not $SkipDocker) {
  Ensure "Docker Desktop" "docker" "Docker.DockerDesktop"
  Write-Host "[note] Docker Desktop needs WSL2 and a reboot on first install. Start it before running the stack."
}

# Python env
if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = Join-Path $root ".venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
if (Test-Path "requirements.txt")     { & $py -m pip install -r requirements.txt }
if (Test-Path "requirements-dev.txt") { & $py -m pip install -r requirements-dev.txt }

# Dashboard deps
if (Test-Path "dashboard\package.json") {
  Push-Location dashboard
  npm install
  Pop-Location
} else { Write-Host "[skip] dashboard/package.json not created yet" }

# Env file
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
  Copy-Item ".env.example" ".env"
  Write-Host "[ok]   .env created from .env.example"
}

# Docker images (best effort)
if (-not $SkipDocker -and (Has "docker") -and (Test-Path "docker-compose.yml")) {
  try { docker compose pull } catch { Write-Host "[warn] docker compose pull failed. Is Docker Desktop running?" }
}

# GitHub auth hint
if (Has "gh") {
  gh auth status 2>$null
  if ($LASTEXITCODE -ne 0) { Write-Host "[todo] Run: gh auth login" }
}

# Smoke test
$hasTests = Get-ChildItem -Recurse -Filter "test_*.py" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\.venv\\" } | Select-Object -First 1
if ($hasTests) { & $py -m pytest -q } else { Write-Host "[skip] no tests yet" }

Write-Host ""
Write-Host "Setup done. Activate env:  .\.venv\Scripts\Activate.ps1"
Write-Host "Workflow skills (optional, once): see docs\WorkflowSetup.md"
Write-Host "Next: read CONTRIBUTING.md and open your issues (label owner:<name>) on GitHub."
