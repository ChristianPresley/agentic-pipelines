#Requires -Version 5.1
<#
.SYNOPSIS
  Builds the hello-api image and runs the E2E suite against it with WSL containers (wslc).
.PARAMETER Engine
  Container CLI to use. Defaults to wslc; pass "docker" to use Docker instead.
#>
[CmdletBinding()]
param(
    [string]$Engine = 'wslc',
    [int]$Port = 8080,
    [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw 'The .NET SDK (see global.json) is required on the host to run the tests.'
}

$image = 'hello-api:e2e-local'
$name = 'hello-api-e2e'

function Invoke-Engine {
    & $Engine @args
    if ($LASTEXITCODE -ne 0) { throw "$Engine $($args -join ' ') failed with exit code $LASTEXITCODE" }
}

Write-Host "Building $image with $Engine"
Invoke-Engine build -t $image .

$ErrorActionPreference = 'Continue'
& $Engine rm -f $name *> $null
$ErrorActionPreference = 'Stop'
try {
    Invoke-Engine run -d --name $name -p "${Port}:8080" $image | Out-Null

    $url = "http://localhost:$Port"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            Invoke-WebRequest "$url/actuator/health/readiness" -UseBasicParsing | Out-Null
            $ready = $true
        } catch {
            $ready = $false
            Start-Sleep -Seconds 2
        }
    } until ($ready -or (Get-Date) -gt $deadline)
    if (-not $ready) {
        & $Engine logs $name
        throw "Container not ready after $TimeoutSeconds seconds"
    }

    $env:E2E_BASE_URL = $url
    & dotnet test tests/HelloApi.Tests/HelloApi.Tests.csproj --filter 'FullyQualifiedName~HelloApiE2ETests'
    if ($LASTEXITCODE -ne 0) { throw 'E2E tests failed' }
} finally {
    $ErrorActionPreference = 'Continue'
    & $Engine rm -f $name *> $null
}
