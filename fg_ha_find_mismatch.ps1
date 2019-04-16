# Identifies checksum mismatches in a FortiGate HA pair. Output is curated for a PRTG sensor.

Param(
    [Parameter(Mandatory=$true)]$address,
    [Parameter(Mandatory=$true)]$username,
    [Parameter(Mandatory=$true)]$password
    )

$SecurePassword = $password | ConvertTo-SecureString -AsPlainText -Force
$Credentials = New-Object System.Management.Automation.PSCredential `
     -ArgumentList $UserName, $SecurePassword
Try{
    New-SSHSession $address -Credential $Credentials -AcceptKey
}
Catch {
    Write-Host "Something went wrong!:WARNING"
    Exit
}

$Session = Get-SSHSession -SessionID 0
        $Stream = $Session.Session.CreateShellStream("dumb", 0, 0, 0, 0, 1000)
        Start-Sleep 1
        $Stream.Write("config global `n")
        Start-Sleep 1
        $Stream.Write("diagnose sys ha checksum cluster `n")
        Start-Sleep 1
$result = $stream.Read()
Remove-SSHSession 0

$check = $result | Select-String -Pattern "all: [a-z0-9 ]{48}" -AllMatches | foreach {$_.Matches} | foreach {$_.Value}


If ($check[1] -ne $check[3])
    {
        $vdoms = $result | Select-String -Pattern ".*: [a-z0-9 ]{48}" -AllMatches | foreach {$_.Matches} | foreach {$_.Value} | sort | Get-Unique
        foreach ($i in $vdoms) {$vdoms[$vdoms.IndexOf($i)] = $i.Substring(0, $i.IndexOf(':')) }
        $vdoms = $vdoms| ? {$_ -ne "all"}
        $mismatchvdoms = (Compare-Object -ReferenceObject $vdoms -DifferenceObject ($vdoms | Get-Unique)).InputObject

        Try{
            New-SSHSession $address -Credential $Credentials -AcceptKey
        }
        Catch {
            Write-Host "Something went wrong!:WARNING"
            Exit
        }
        $Session = Get-SSHSession -SessionID 0
            $Stream = $Session.Session.CreateShellStream("dumb", 0, 0, 0, 0, 1000)
            Start-Sleep 1
            $Stream.Write("config global `n")
            Start-Sleep 1
            $Stream.Write("diagnose sys ha checksum show $mismatchvdoms `n")
            Start-Sleep 1
            $primaryraw = $stream.Read()
            Start-Sleep 1
            $Stream.Write("execute ha manage 0 `n")
            Start-Sleep 1
            $Stream.Write("$username`n")
            Start-Sleep 1
            $Stream.Write("$password`n")
            Start-Sleep 1
            $Stream.Write("config global `n")
            Start-Sleep 1
            $Stream.Write("diagnose sys ha checksum show $mismatchvdoms `n")
            Start-Sleep 1
            $secondaryraw = $stream.Read()
            Remove-SSHSession 0
           
            $primaryconfig = $primaryraw | Select-String -Pattern ".*: [a-f0-9 ]{32}" -AllMatches | foreach {$_.Matches} | foreach {$_.Value}
            $secondaryconfig = $secondaryraw | Select-String -Pattern ".*: [a-f0-9 ]{32}" -AllMatches | foreach {$_.Matches} | foreach {$_.Value}
            $conflict = $primaryconfig | ? {$secondaryconfig -notcontains $_}

            Write-Output "Mismatch found in $mismatchvdoms`: $conflict"
    }

Else
    {
        Write-Output "No mismatches found."
     }
