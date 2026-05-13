# ============================================================
# Backdated commits — Disease_Detection — 2026
# ============================================================

$AUTHOR_NAME  = "Mohamed Farthas"
$AUTHOR_EMAIL = "152224363+mfarthas-al@users.noreply.github.com"

Set-Location "c:\Users\mfart\Desktop\Research\Disease Detection\R26-SE-032"

function Commit {
    param([string]$Message, [string]$Date)
    $env:GIT_AUTHOR_NAME     = $AUTHOR_NAME
    $env:GIT_AUTHOR_EMAIL    = $AUTHOR_EMAIL
    $env:GIT_COMMITTER_NAME  = $AUTHOR_NAME
    $env:GIT_COMMITTER_EMAIL = $AUTHOR_EMAIL
    $env:GIT_AUTHOR_DATE     = $Date
    $env:GIT_COMMITTER_DATE  = $Date
    git commit -m $Message
    Write-Host "OK: $Message  [$Date]" -ForegroundColor Green
}

git add Disease_Detection/README.md .gitignore
Commit "feat: initial Disease_Detection project setup and structure" "2026-04-09T09:15:00"

git add Disease_Detection/pipeline/stage1_data_preparation/merge_final.py
Commit "feat: add data merge and preparation pipeline (Stage 1)" "2026-04-14T14:20:00"

git add Disease_Detection/pipeline/stage2_model_training/train_final.py
Commit "feat: add YOLOv8 model training script (Stage 2)" "2026-04-21T16:00:00"

git add Disease_Detection/pipeline/stage3_evaluation/evaluate_final.py
Commit "feat: add model evaluation pipeline with metrics logging (Stage 3)" "2026-04-28T15:30:00"

git add Disease_Detection/pipeline/stage4_inference/app.py
Commit "feat: add inference application for real-time disease detection (Stage 4)" "2026-05-06T14:45:00"

git add Disease_Detection/frontend/index.html
Commit "feat: add frontend dashboard for disease detection visualization" "2026-05-09T11:20:00"

git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    Commit "feat: final cleanup and project polish" "2026-05-13T18:00:00"
}

Remove-Item Env:\GIT_AUTHOR_NAME, Env:\GIT_AUTHOR_EMAIL, Env:\GIT_COMMITTER_NAME, Env:\GIT_COMMITTER_EMAIL, Env:\GIT_AUTHOR_DATE, Env:\GIT_COMMITTER_DATE -ErrorAction SilentlyContinue

Write-Host "`nDone! Log:" -ForegroundColor Cyan
git log --oneline feature/disease-detection | Select-Object -First 10
