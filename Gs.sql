

function Get-FolderCount($Cat) {
    $raw = gcloud storage ls --recursive "$basePath/$Cat/**"
    if ($raw.Count -eq 0) { return 0 }
    $unique = $raw | ForEach-Object {
        $rel = $_ -replace "^.*$Cat/", ""
        $p = $rel.Split('/')
        if ($p.Count -ge 2) { "$($p[0])/$($p[1])" }
    } | Select-Object -Unique
    return ($unique | Measure-Object).Count
}


$summary = [PSCustomObject]@{
    Extracted = Get-FolderCount "Extracted"
    Processed = Get-FolderCount "Processed"
    Error     = Get-FolderCount "Error"
    Archive   = Get-FolderCount "Archive"
}


Write-Host "--- [TABLE 1] TOTAL JOB INVENTORY (Unique Folders) ---" -ForegroundColor Yellow
$summary | Format-Table -AutoSize


function Get-MailJobStats($Category) {
    Write-Host "`n--- [TABLE] GRANULAR VIEW: $Category ---" -ForegroundColor Yellow
    
    $fullUrl = "$basePath/$Category/**"
    $rawFiles = gcloud storage ls --recursive $fullUrl
    
    if ($rawFiles.Count -eq 0) {
        Write-Host "No data found in $Category." -ForegroundColor Gray
        return
    }

    $uniqueJobs = $rawFiles | ForEach-Object {
        $rel = $_ -replace "^.*$Category/", ""
        $parts = $rel.Split('/')
        if ($parts.Count -ge 2) { "$($parts[0])|$($parts[1])" }
    } | Select-Object -Unique

    $uniqueJobs | ForEach-Object {
        [PSCustomObject]@{ Date = $_.Split('|')[0] }
    } | Group-Object Date | Select-Object `
        @{N="Date"; E={$_.Name}}, 
        @{N="Mail_Folders_Count"; E={$_.Count}} | 
        Sort-Object Date -Descending | 
        Format-Table -AutoSize
}


Get-MailJobStats "Extracted"
Get-MailJobStats "Error"
Get-MailJobStats "Archive"


Write-Host "`n✅ Report Complete." -ForegroundColor Green
-- File cleared
