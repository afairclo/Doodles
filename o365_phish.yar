rule o365_phish
{
	strings:
		$a = "Login with Office 365" nocase
		$b = "Login with Outlook" nocase
		$c = "to listen to the voice mail" nocase
		$d = "Work Microsoft account" nocase
		$e = "choose your email provider" nocase
		
	condition:
		2 of ($a,$b,$c,$d,$e)
}