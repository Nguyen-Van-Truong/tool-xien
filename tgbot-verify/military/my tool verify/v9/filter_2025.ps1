$inputFile = "E:\tool xien\tgbot-verify\military\my tool verify\v9_cuaDungpham_tool_signup_ver\all_veterans.txt"
$content = Get-Content $inputFile
$before = $content.Count
# Filter out lines ending with |2000, |2001, ... |2025 (years 2000-2025)
$filtered = $content | Where-Object { $_ -notmatch '\|(20[0-2][0-9])$' }
$filtered | Set-Content $inputFile
$after = $filtered.Count
Write-Host "Removed $($before - $after) lines with birth year 2000-2025. Before: $before After: $after"
