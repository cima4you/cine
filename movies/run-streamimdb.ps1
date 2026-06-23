param(
    [int]$StartPage = 1,
    [int]$EndPage = 0,
    [int]$Parallel = 5
)

$ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$SCRAPER = "$ROOT\screpte\streamimdb\scrape_streamimdb.py"
$CONVERT = "$ROOT\screpte\streamimdb\convert_to_js.py"

Write-Host "========== StreamIMDb ==========" -ForegroundColor Cyan
Write-Host "Pages: $StartPage - $(if ($EndPage -eq 0) { 'end' } else { $EndPage })" -ForegroundColor Yellow

$pageToArg = if ($EndPage -gt 0) { "--page-to", $EndPage } else { @() }

python -X utf8 $SCRAPER --page-from $StartPage @pageToArg --resume --parallel $Parallel
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

python -X utf8 $CONVERT
if ($LASTEXITCODE -ne 0) { Write-Host "Convert FAILED" -ForegroundColor Red; exit 1 }

Write-Host "`nDone! Now commit and push:" -ForegroundColor Green
Write-Host "git add -A && git commit -m `"تحديث StreamIMDb`" && git push" -ForegroundColor White
