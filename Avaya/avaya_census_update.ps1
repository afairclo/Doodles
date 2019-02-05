# Updates Avaya full names for resident phones based on CSV census file.
# Use on secure connections only

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$avaya1 = $null
$avaya2 = $null
$dstip = "phones.mycompany.org"

$CSV = ".\census.csv"

# Format names to FirstName Lastname

$census = Import-Csv $CSV | ? NurStn -like "*R*" | foreach { 
    $_.Name = "{1} {0}" -f ($_.Name -split ', ')
    $_ 
    }

# Authenticate to API

# Use "Basic {Base64 UTF-8 encoded "username:password"}" for Authorization header.
# Ex. "Basic YWRtaW46cGFzc3dvcmQ="
# Decoded: "Basic admin:password"

$headers=@{`
    "Content-Type" = "application/json";`
    "X-User-Client" = "Avaya-WebAdmin";`
    "X-User-Agent" = "Avaya-SDKUser";`
    "Authorization" = ""`
    }

$uri="https://$dstip`:7070/WebManagement/ws/sdk/security/authenticate"

Try {
        $data = $null
        $data = Invoke-Webrequest -Method Get -Uri $uri -Headers $headers -SessionVariable avaya
    }
Catch {
        Write-Output "$((Get-Date).DateTime) Connection error. [SETUP] $($Error[0].ErrorDetails.Message)"
        Return
    }

$sessionID = $data.Headers.'Set-Cookie'
$sessionID = $data.Headers.'Set-Cookie'.Substring(0, $sessionID.IndexOf(';'))

$headers2=@{`
    "Content-Type" = "application/json";`
    "X-User-Client" = "Avaya-WebAdmin";`
    "X-User-Agent" = "Avaya-SDKUser";`
    "Cookie" = "$sessionID"`
    }

$uri2="https://$dstip`:7070/WebManagement/ws/sdk/admin/v1/users"

# Get users

Try {
    $data2 = Invoke-WebRequest -Method Get -Uri $uri2 -Headers $headers2 -ContentType 'application/json' -WebSession $avaya
    }
Catch {
    Write-Output "$((Get-Date).DateTime) Connection error. [PULL] $($Error[0].ErrorDetails.Message) [$sessionID]"
    Return
    }
$users = ConvertFrom-Json $data2.Content
$users = $users.response.data.ws_object

$psusers = @()

# Format result to PSObject

foreach ($user in $users)
    {
       $temp = New-Object PSObject
       $temp | Add-Member NoteProperty Username $user.User.Name
       $temp | Add-Member NoteProperty Extension $user.User.Extension
       $temp | Add-Member NoteProperty FullName $user.User.FullName
       $temp | Add-Member NoteProperty GUID $user.User.'@GUID'

       $psusers += $temp
}

# Update users

foreach ($resident in $census) {
    
    $targetGUID = ($psusers | ? Username -like "*$($resident.Room)*").GUID
    # Check for duplicates. Specify A/B if so.
    If (($targetGUID | measure).Count -ne 1) {
        $targetGUID = ($psusers | ? Username -like "*$($resident.Room)$($resident.Bed)*").GUID
        Write-Output "Updating $($resident.Name) in room $($resident.Room)$($resident.Bed).."
        $room = "$($resident.Room)$($resident.Bed)"
        }
    Else {
    $room = $resident.Room
    Write-Output "Updating $($resident.Name) in room $room.."
        }
    $targetExtension = ($psusers | ? GUID -eq $targetGUID).Extension
    
    # WARNING: If these attributes not set, they will be CLEARED

    $json = @{
                    "data" = @{
                        "ws_object" = @{
                            "User" = @{
                                "@GUID" = "$targetGUID";
                                "Extension" = $targetExtension;
                                "FullName" = "Room $room $($resident.Name)";
                                "Password" = "RiverGarden1"
                                "Name" = "$(($psusers | ? GUID -eq $targetGUID).Username)";
                                "VoicemailOn" = $false;
                                "BlockForwarding" = $true
                                }
                            }
                        }
                    }
                
    $input_data = ConvertTo-Json $json -Depth 50
    
    $uri2="https://$dstip`:7070/WebManagement/ws/sdk/admin/v1/users"

    # Add same authorizaiton from above.

    $headers2=@{`
        "Content-Type" = "application/json";`
        "X-User-Client" = "Avaya-WebAdmin";`
        "X-User-Agent" = "Avaya-SDKUser";`
        "Authorization" = ""`
        }
    Try {
        $data2 = Invoke-Webrequest -Method PUT -Uri $uri2 -Headers $headers2 -WebSession $avaya -Body $input_data
        }
    Catch {
        Write-Output "$((Get-Date).DateTime) Connection error. [PUT] $($Error[0].ErrorDetails.Message) [$sessionID]"
        Return
        }
  }