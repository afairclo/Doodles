[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$places = Import-Csv C:\scripts\LunchBot\places.csv
$history = Import-Csv C:\scripts\LunchBot\history.csv
$picked = $false
$tries = 0

Import-Module PSSlack
$slackuri = ""
$channel = ""

# Sushi Wednesday
If ($(Get-Date).DayOfWeek -eq "Wednesday") {
    $pick = $places | ? Venue -like "*Fuji*"
    $picked = $true
    }

# Limit to be equal to or less than your total venues
$lastPicks = $history | ? Date -gt $(Get-Date).AddDays(-12) | Select -Last 10

# Exclusion list
$candidates = $places | ? Venue -notlike "*Fuji*"

# Pick loop
While ($picked -eq $false) {

    $test = $null
    # Try this one
    $pick = $candidates | Get-Random

    $test = $lastPicks | ? Genre -like "$($pick.Genre)"

    If ($test -eq $null)
        {
        $pick = $candidates | ? Genre -like "$($pick.Genre)" | Get-Random
        $picked = $true
        }

    $tries++
    # Timeout
    If ($tries -gt $($places | measure).Count)
        {$picked = $true}
    }

Write-Output "Pick: $($pick.Venue) ($($pick.Genre), $($tries) tries)"

# Send to Slack, don't save if it doesn't send
Try {
    Send-SlackMessage -Uri $slackuri -Channel $channel -Text $pick.Venue -ErrorVariable SendSlack
    $addHistory = "{0},{1},{2}" -f $(Get-Date),$pick.Venue,$pick.Genre
    $addHistory | Add-Content -Path C:\scripts\LunchBot\history.csv
    }
Catch {
    Write-Output "Send failed. $sendslack" 
    }
