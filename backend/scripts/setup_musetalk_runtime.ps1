param(
  [string]$PythonLauncher = "py -3.10",
  [string]$RuntimeRoot = "",
  [string]$VenvRoot = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) {
  $RuntimeRoot = Join-Path $repoRoot ".runtime\\MuseTalk"
}
if ([string]::IsNullOrWhiteSpace($VenvRoot)) {
  $VenvRoot = Join-Path $repoRoot ".venv-musetalk"
}

$runtimePath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RuntimeRoot)
$venvPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($VenvRoot)
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"
$pipExe = Join-Path $venvPath "Scripts\\pip.exe"

function Invoke-Step {
  param(
    [string]$Title,
    [scriptblock]$Action
  )

  Write-Host ""
  Write-Host "==> $Title" -ForegroundColor Cyan
  & $Action
  if ($LASTEXITCODE -ne 0) {
    throw "Step failed: $Title (exit code $LASTEXITCODE)"
  }
}

Invoke-Step "Preparing MuseTalk runtime directories" {
  New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
}

if (-not (Test-Path (Join-Path $runtimePath ".git"))) {
Invoke-Step "Cloning official MuseTalk repository" {
  git clone https://github.com/TMElyralab/MuseTalk.git $runtimePath
}
}
else {
  Invoke-Step "Updating MuseTalk repository" {
    git -C $runtimePath pull --ff-only
  }
}

if (-not (Test-Path $pythonExe)) {
  Invoke-Step "Creating dedicated MuseTalk Python 3.10 virtual environment" {
    Invoke-Expression "$PythonLauncher -m venv `"$venvPath`""
  }
}

Invoke-Step "Upgrading pip tooling" {
  & $pythonExe -m pip install --upgrade pip setuptools wheel
}

Invoke-Step "Installing CUDA-enabled PyTorch (official MuseTalk baseline)" {
  & $pipExe install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
}

Invoke-Step "Installing MuseTalk Python dependencies" {
  & $pipExe install -r (Join-Path $runtimePath "requirements.txt")
}

Invoke-Step "Installing OpenMMLab stack required by MuseTalk" {
  & $pipExe install --no-cache-dir -U openmim
  if ($LASTEXITCODE -ne 0) { throw "Failed to install openmim." }
  & $pythonExe -m mim install mmengine
  if ($LASTEXITCODE -ne 0) { throw "Failed to install mmengine." }
  & $pythonExe -m mim install "mmcv==2.0.1"
  if ($LASTEXITCODE -ne 0) { throw "Failed to install mmcv==2.0.1." }
  & $pythonExe -m mim install "mmdet==3.1.0"
  if ($LASTEXITCODE -ne 0) { throw "Failed to install mmdet==3.1.0." }
  & $pipExe install chumpy==0.70 --no-build-isolation
  if ($LASTEXITCODE -ne 0) { throw "Failed to install chumpy==0.70." }
  & $pythonExe -m mim install "mmpose==1.1.0" --no-build-isolation
  if ($LASTEXITCODE -ne 0) { throw "Failed to install mmpose==1.1.0." }
}

Invoke-Step "Downloading MuseTalk 1.5 weights from official sources" {
  Push-Location $runtimePath
  try {
    cmd /c download_weights.bat
    if ($LASTEXITCODE -ne 0) { throw "Failed to download MuseTalk weights." }
    $env:HF_ENDPOINT = "https://hf-mirror.com"
    hf download stabilityai/sd-vae-ft-mse config.json --local-dir (Join-Path $runtimePath "models\\sd-vae")
    if ($LASTEXITCODE -ne 0) { throw "Failed to download sd-vae config.json." }
    hf download openai/whisper-tiny config.json --local-dir (Join-Path $runtimePath "models\\whisper")
    if ($LASTEXITCODE -ne 0) { throw "Failed to download whisper config.json." }
    hf download ManyOtherFunctions/face-parse-bisent 79999_iter.pth --local-dir (Join-Path $runtimePath "models\\face-parse-bisent")
    if ($LASTEXITCODE -ne 0) { throw "Failed to download face-parse-bisent 79999_iter.pth." }
  }
  finally {
    Pop-Location
  }
}

Write-Host ""
Write-Host "MuseTalk runtime bootstrap finished." -ForegroundColor Green
Write-Host "Set these environment variables before starting the backend:" -ForegroundColor Yellow
Write-Host "  MUSE_TALK_ENABLED=1"
Write-Host "  MUSE_TALK_PYTHON_PATH=$pythonExe"
Write-Host "  MUSE_TALK_PROJECT_DIR=$runtimePath"
Write-Host "  MUSE_TALK_RESULT_DIR=$(Join-Path $repoRoot 'generated\\musetalk')"
Write-Host "  MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE=$(Join-Path $repoRoot 'assets\\musetalk\\verba_tutor.png')"
