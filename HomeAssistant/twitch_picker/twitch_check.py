@service
def twitch_check(action=None, id=None):
    import json
    import requests

# Tests updated stream details against original stream details.
# If the game is no longer current, find a new stream via twitch_picker.py
# Runs every 5 minutes, 30 minutes after a stream is picked.

    requestHeaders = {
        'Authorization':'Bearer ' + input_text.twitch_oauth_token,
        'Client-Id':str(input_text.twitch_client_id)
        }
        
    pickURL = "https://api.twitch.tv/helix/streams?user_login="+input_text.twitch_picker
    response = task.executor(requests.get, pickURL, headers=requestHeaders)
    pickJson = response.json()
    
    if not pickJson['data']:
        service.call("pyscript", "twitch_picker")
        exit()
    
    for pick_info in pickJson['data']:
        input_text.twitch_picker_title.set_value(pick_info['title']+" 🔴 "+str(pick_info['viewer_count']))
        if pick_info['game_name'] != input_text.twitch_picker_game:
            service.call("pyscript", "twitch_picker")