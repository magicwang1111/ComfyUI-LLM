param(
    [int]$Port = 8195,
    [string]$BaseUrl = 'http://127.0.0.1:8180',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
if ($Port -ge 8180 -and $Port -le 8190) { throw 'Agent service must not use ports 8180-8190.' }
if (-not $Python) {
    $Python = Join-Path $PSScriptRoot '.agent_env\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $Python)) { $Python = (Get-Command python -ErrorAction Stop).Source }
}
& $Python (Join-Path $PSScriptRoot 'agent_service.py') --port $Port --base-url $BaseUrl
exit $LASTEXITCODE
