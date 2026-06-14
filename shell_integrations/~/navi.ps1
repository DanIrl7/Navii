
function navi {
    $projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
    $pythonExecutable = (Join-Path $projectRoot ".venv\Scripts\python.exe")

    if (-not (Test-Path $pythonExecutable)) {
        $pythonExecutable = "python.exe"
    }

    $oldPath = $env:PYTHONPATH
    $env:PYTHONPATH = $projectRoot
    $selected_dir = & $pythonExecutable -m src.navii.main
    $env:PYTHONPATH = $oldPath

    if ($selected_dir) {
        Set-Location $selected_dir
    }
}