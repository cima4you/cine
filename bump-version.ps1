param(
    [string]$Message = "تحديث"
)

$ROOT = Split-Path -Parent $PSCommandPath
$INDEX = "$ROOT\index.html"

# Read current version
$content = Get-Content -Path $INDEX -Raw
$match = [regex]::Match($content, 'v=(\d+)([a-z]+)')

if (-not $match.Success) {
    Write-Host 'ERROR: Version not found' -ForegroundColor Red
    exit 1
}

$num = $match.Groups[1].Value
$letter = $match.Groups[2].Value
$oldVer = $num + $letter

# Bump letter: e.g., h -> i, z -> aa
$newLetter = ''
$carry = $true
for ($i = $letter.Length - 1; $i -ge 0; $i--) {
    if ($carry) {
        $c = [char]([int][char]$letter[$i] + 1)
        if ($c -gt 'z') {
            $newLetter = 'a' + $newLetter
        } else {
            $newLetter = $c + $newLetter
            $carry = $false
        }
    } else {
        $newLetter = $letter[$i] + $newLetter
    }
}
if ($carry) { $newLetter = 'aa' + $newLetter }

$newVer = $num + $newLetter

$content = $content -replace "v=$oldVer", "v=$newVer"
[System.IO.File]::WriteAllText($INDEX, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "Version: $oldVer → $newVer" -ForegroundColor Green

# Git operations
git add -A
git commit -m "$Message"
git add -A
git commit -m "bump version $newVer"
git push
