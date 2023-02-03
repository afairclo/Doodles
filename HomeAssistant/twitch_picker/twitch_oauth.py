@service
def twitch_oauth(action=None, id=None):
    import json
    import requests

# Refreshes Twitch oauth token. Runs every 20 days. 
# Requires helpers for client ID and secret in Home Assistant.

    tokenURL = "https://id.twitch.tv/oauth2/token"
    
    body = {
        'client_id':str(input_text.twitch_client_id),
        'client_secret':str(input_text.twitch_client_secret),
        'grant_type': 'client_credentials'
        }
    
    response = task.executor(requests.post, tokenURL, body)
    tokenResponse = response.json()
    input_text.twitch_oauth_token.set_value(tokenResponse['access_token'])