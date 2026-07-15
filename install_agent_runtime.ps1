$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Environment = Join-Path $Root ".agent_env"
python -m venv $Environment
& (Join-Path $Environment "Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $Environment "Scripts\python.exe") -m pip install -r (Join-Path $Root "requirements-agent.txt")
Write-Host "Agent SDK runtime installed at $Environment"

