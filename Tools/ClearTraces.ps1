# Deletes every Unreal Insights trace in the local trace store.
# Close Unreal Insights and the editor first: while either is open, the store can be in use
# (and the editor records into it whenever Insights is running).

$store = Join-Path $env:LOCALAPPDATA "UnrealEngine\Common\UnrealTrace\Store"

if (Get-Process UnrealInsights, UnrealEditor -ErrorAction SilentlyContinue) {
    Write-Host "Close Unreal Insights and the editor first, then run this again."
    exit 1
}

$traces = Get-ChildItem $store -Recurse -Include *.utrace, *.ucache -File -ErrorAction SilentlyContinue
if (-not $traces) {
    Write-Host "No traces in $store."
    exit 0
}

$size = ($traces | Measure-Object Length -Sum).Sum / 1GB
Write-Host ("Deleting {0} file(s), {1:N1} GB, from {2}" -f $traces.Count, $size, $store)
$traces | Remove-Item -ErrorAction Continue
Write-Host "Done."
