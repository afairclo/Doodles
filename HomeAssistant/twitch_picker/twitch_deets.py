@service
def twitch_deets(action=None, id=None):
    import json
    import requests

    requestHeaders = {
        'Authorization':'Bearer ' + input_text.twitch_oauth_token,
        'Client-Id':str(input_text.twitch_client_id)
        }
        
    pickURL = "https://api.twitch.tv/helix/streams?user_login="+input_text.twitch_picker
    response = task.executor(requests.get, pickURL, headers=requestHeaders)
    pickJson = response.json()
    
    for pick_info in pickJson['data']:
        input_text.twitch_picker_game.set_value(pick_info['game_name'])
        input_text.twitch_picker_title.set_value(pick_info['title'])
        input_text.twitch_picker_chat.set_value("https://www.giambaj.it/twitch/jchat/v2/?channel="+pick_info['user_name']+"&hide_commands=true&size=1&font=2")

    # Get user avatar
   
    pickURL = "https://api.twitch.tv/helix/users?login="+input_text.twitch_picker
    response = task.executor(requests.get, pickURL, headers=requestHeaders)
    pickJson = response.json()
    
    for pick_info in pickJson['data']:
        input_text.twitch_picker_avatar.set_value(pick_info['profile_image_url'])
		