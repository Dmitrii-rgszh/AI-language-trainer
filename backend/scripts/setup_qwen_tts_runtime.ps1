$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Split-Path -Parent $scriptDir
$venvPath = Join-Path $backendDir ".venv-qwen"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pipExe = Join-Path $venvPath "Scripts\pip.exe"

if (-not (Test-Path $venvPath)) {
  Write-Host "[STEP] Creating Qwen3-TTS virtualenv..."
  py -3.10 -m venv $venvPath
}

Write-Host "[STEP] Upgrading pip..."
& $pythonExe -m pip install --upgrade pip

Write-Host "[STEP] Installing CUDA-enabled PyTorch for Qwen3-TTS..."
& $pipExe install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

Write-Host "[STEP] Installing Qwen3-TTS sidecar dependencies..."
& $pipExe install --upgrade qwen-tts fastapi uvicorn

Write-Host "[STEP] Verifying torch CUDA access..."
& $pythonExe -c "import torch; print('cuda_available=', torch.cuda.is_available()); print('device_count=', torch.cuda.device_count())"

Write-Host "[OK] Qwen3-TTS runtime setup completed."
