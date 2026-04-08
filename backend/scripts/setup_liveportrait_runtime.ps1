param(
  [string]$PythonLauncher = "py -3.10",
  [string]$RuntimeRoot = "",
  [string]$VenvRoot = "",
  [string]$AvatarAssetDir = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$defaultRuntimeHome = Join-Path $env:LOCALAPPDATA "CodexLivePortrait"
if ([string]::IsNullOrWhiteSpace($RuntimeRoot)) {
  $RuntimeRoot = Join-Path $defaultRuntimeHome "LivePortrait"
}
if ([string]::IsNullOrWhiteSpace($VenvRoot)) {
  $VenvRoot = Join-Path $defaultRuntimeHome ".venv-liveportrait"
}
if ([string]::IsNullOrWhiteSpace($AvatarAssetDir)) {
  $AvatarAssetDir = Join-Path $repoRoot "assets\\live_avatar\\verba_tutor"
}

$runtimePath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($RuntimeRoot)
$venvPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($VenvRoot)
$avatarAssetPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($AvatarAssetDir)
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"
$pipExe = Join-Path $venvPath "Scripts\\pip.exe"
$hfCli = Join-Path $venvPath "Scripts\\huggingface-cli.exe"
$hfExe = Join-Path $venvPath "Scripts\\hf.exe"
$defaultIdleDriving = Join-Path $avatarAssetPath "idle_driving.mp4"
$bundledIdleDriving = Join-Path $runtimePath "assets\\examples\\driving\\d9.mp4"

function Invoke-Step {
  param(
    [string]$Title,
    [scriptblock]$Action
  )

  Write-Host ""
  Write-Host "==> $Title" -ForegroundColor Cyan
  & $Action
  if ((-not [string]::IsNullOrWhiteSpace("$LASTEXITCODE")) -and $LASTEXITCODE -ne 0) {
    throw "Step failed: $Title (exit code $LASTEXITCODE)"
  }
}

Invoke-Step "Preparing LivePortrait runtime directories" {
  New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
  New-Item -ItemType Directory -Force -Path $avatarAssetPath | Out-Null
}

if (-not (Test-Path (Join-Path $runtimePath ".git"))) {
  Invoke-Step "Cloning official LivePortrait repository" {
    git clone https://github.com/KlingTeam/LivePortrait.git $runtimePath
  }
}
else {
  Invoke-Step "Updating LivePortrait repository" {
    git -C $runtimePath pull --ff-only
  }
}

if (-not (Test-Path $pythonExe)) {
  Invoke-Step "Creating dedicated LivePortrait Python 3.10 virtual environment" {
    Invoke-Expression "$PythonLauncher -m venv `"$venvPath`""
  }
}

Invoke-Step "Upgrading pip tooling" {
  & $pythonExe -m pip install --upgrade pip setuptools wheel
}

Invoke-Step "Installing CUDA-enabled PyTorch for LivePortrait" {
  & $pipExe install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu121
}

Invoke-Step "Installing LivePortrait Python dependencies" {
  & $pipExe install -r (Join-Path $runtimePath "requirements.txt")
}

Invoke-Step "Installing Hugging Face CLI" {
  & $pipExe install "huggingface_hub[cli]"
}

Invoke-Step "Downloading official LivePortrait weights" {
  $env:PYTHONUTF8 = "1"
  $env:PYTHONIOENCODING = "utf-8"
  if (Test-Path $hfExe) {
    & $hfExe download KlingTeam/LivePortrait --local-dir (Join-Path $runtimePath "pretrained_weights") --exclude "*.git*" "README.md" "docs"
  }
  else {
    & $hfCli download KlingTeam/LivePortrait --local-dir (Join-Path $runtimePath "pretrained_weights") --exclude "*.git*" "README.md" "docs"
  }
}

if ((-not (Test-Path $defaultIdleDriving)) -and (Test-Path $bundledIdleDriving)) {
  Invoke-Step "Bootstrapping canonical idle driving clip from bundled LivePortrait example" {
    & ffmpeg -y -ss 0 -t 4 -i $bundledIdleDriving -an $defaultIdleDriving
  }
}

Write-Host ""
Write-Host "LivePortrait runtime bootstrap finished." -ForegroundColor Green
Write-Host "Set these environment variables before starting the backend:" -ForegroundColor Yellow
Write-Host "  LIVE_AVATAR_LIVEPORTRAIT_ENABLED=1"
Write-Host "  LIVE_AVATAR_LIVEPORTRAIT_PYTHON_PATH=$pythonExe"
Write-Host "  LIVE_AVATAR_LIVEPORTRAIT_PROJECT_DIR=$runtimePath"
Write-Host "  LIVE_AVATAR_IDLE_DRIVING_VIDEO=$defaultIdleDriving"
