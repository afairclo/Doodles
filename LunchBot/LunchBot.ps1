[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$places = Import-Csv C:\scripts\LunchBot\places.csv
$history = Import-Csv C:\scripts\LunchBot\history.csv
$picked = $false
$tries = 0

Import-Module PSSlack
$slackuri = ""
$channel = ""

# Convert history dates to DateTime
foreach ($entry in $history) {
    $entry.Date = [Datetime]$entry.Date
    }

# Limit to be equal to or less than your total venues
$lastPicks = $history | ? Date -gt $(Get-Date).AddDays(-12)

$candidates = $places  | ? {$lastPicks.Genre -notcontains $_.Genre} | ? {$lastPicks.Venue -notcontains $_.Venue}

$pick = $candidates | Get-Random

# Sushi Wednesday
If ($(Get-Date).DayOfWeek -eq "Wednesday") {
    $pick = $places | ? Venue -like "*Fuji*"
    }

Write-Output "Pick: $($pick.Venue) ($($pick.Genre)"

# Send to Slack, don't save if it doesn't send
Try {
    Send-SlackMessage -Uri $slackuri -Channel $channel -Text $pick.Venue -ErrorVariable SendSlack
    $addHistory = "{0},{1},{2}" -f $(Get-Date),$pick.Venue,$pick.Genre
    $addHistory | Add-Content -Path C:\scripts\LunchBot\history.csv
    }
Catch {
    Write-Output "Send failed. $sendslack" 
    }
