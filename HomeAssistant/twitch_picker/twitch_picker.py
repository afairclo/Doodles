@service
def twitch_picker(action=None, id=None):
    import json
    import requests
    import random
    import urllib.parse
    import asyncio
    
    #entity_id = data.get("entity_id")
    entity_id = "media_player.man_cave"
    
    # Twitch OAuth
    requestHeaders = {
        'Authorization':'Bearer ' + input_text.twitch_oauth_token,
        'Client-Id':str(input_text.twitch_client_id)
        }
       
    streamers = []
    pick = None
    
    # Get top stream. If they have over 300k viewers, stream it.
    requestURL = "https://api.twitch.tv/helix/streams?language=en&first=1"
    response = task.executor(requests.get, requestURL, headers=requestHeaders)
    streams = response.json()
    for stream in streams['data']:
        if stream['viewer_count'] >= 300000:
            pick = stream['user_login']
        else:
            topStream = stream['user_login']
    
    # Pick Routine
    
    if pick == None:
    
        gameIDs = [
            '493388', # Foxhole
            '15467', # Battlefield 2
            '16348', # Battlefield 2142
            '920937099', # Darts
            '7193', # Microsoft Flight Simulator
            '22038', # Natural Selection 2
            '8882', # Pinball
            '512971', # Chivalry II
            '1095275650', # Hogwarts Legacy
            '847542703' # Train Sim World 3
            ]
        
        if person.brendon == "home":
            gameIDs.append('508455') # Valheim
            gameIDs.append('743214338') # Brotato
            gameIDs.append('515621883') # Soulstone Surviors
            gameIDs.remove('493388') # Foxhole
            gameIDs.remove('847542703') # Train Sim World 3
        
        chartGames = []
        
        # Append Steam Charts' top trending game to game list
        steamcharts = urllib.parse.quote(sensor.steam_charts_top_trending_game)
        chartGames.append(steamcharts)
        
        # Steam250 Trending
        steam250_trending = urllib.parse.quote(sensor.steam250_trending)
        chartGames.append(steam250_trending)
        
        # Steam250 Top Week
        steam250_topweek = urllib.parse.quote(sensor.steam250_week_top_30)
        chartGames.append(steam250_topweek)
        
        # Steam250 On Sale
        steam250_onsale = urllib.parse.quote(sensor.steam250_on_sale)
        chartGames.append(steam250_onsale)
        
        # Steam 250 Under 5
        steam250_under5 = urllib.parse.quote(sensor.steam250_under_5)
        chartGames.append(steam250_under5)
        
        # Skip trending games not interested in
        
        skipGames = [
            urllib.parse.quote('Mount & Blade II: Bannerlord'),
            urllib.parse.quote('Portal 2'),
            urllib.parse.quote('Vampire Survivors'),
            urllib.parse.quote('Warhammer 40,000: Darktide'),
            urllib.parse.quote('Gorilla Tag'),
            urllib.parse.quote('Euro Truck Simulator 2')
            ]
        
        for chartGame in chartGames:
            if chartGame not in skipGames:
                requestURL = "https://api.twitch.tv/helix/games?name="+chartGame
                response = task.executor(requests.get, requestURL, headers=requestHeaders)
                trendingJson = response.json()
                for trendingGame in trendingJson['data']:
                    gameIDs.append(trendingGame['id'])
        
        # Pick loop
        input_number.twitch_picker_loops.set_value(0)
        loops = 0
        while len(streamers) == 0:
            loops += 1
            input_number.twitch_picker_loops.set_value(loops)
            # Pick a game
            chosenGame = random.choice(gameIDs)
            
            skipList = [
                'presscorps',
                'bf2tv',
                'saltybet',
                'rlgym',
                'xfearxireaper'
                ]

            # Get stream candidates, top 10 English streamers for chosen game
            requestURL = "https://api.twitch.tv/helix/streams?game_id="+chosenGame+"&language=en&first=10"
            response = task.executor(requests.get, requestURL, headers=requestHeaders)
            streams = response.json()
            for stream in streams['data']:
                if stream['user_login'] not in skipList:
                    if stream['tags'] != None:
                        # Filter out VTubers. Sorry, not sorry.
                        tags_formatted = []
                        for tag in stream['tags']:
                            tags_formatted.append(tag.lower())
                        if tags_formatted.count("vtuber")==0:
                            streamers.append(stream['user_login'])
                    else:
                        streamers.append(stream['user_login'])
                        
        # print(streamers)
        input_number.twitch_picker_results.set_value(len(streamers))
        
        # Add top streamer if the stream isn't rare.
        if len(streamers) > 5:
            streamers.append(topStream)
        
        pick = random.choice(streamers)
    
    # Get stream info
    
    pickURL = "https://api.twitch.tv/helix/streams?user_login="+pick
    response = task.executor(requests.get, pickURL, headers=requestHeaders)
    pickJson = response.json()
    
    for pick_info in pickJson['data']:
        input_text.twitch_picker.set_value(pick_info['user_name'])
        input_text.twitch_picker_game.set_value(pick_info['game_name'])
        input_text.twitch_picker_title.set_value(pick_info['title']+" 🔴 "+str(pick_info['viewer_count']))
        input_text.twitch_picker_chat.set_value("https://www.giambaj.it/twitch/jchat/v2/?channel="+pick_info['user_name']+"&hide_commands=true&size=1&font=2")
        input_text.twitch_picker_chat_popout.set_value("https://www.twitch.tv/popout/"+pick_info['user_name']+"/chat?popout=")
   
   # Get user avatar
   
    pickURL = "https://api.twitch.tv/helix/users?login="+pick
    response = task.executor(requests.get, pickURL, headers=requestHeaders)
    pickJson = response.json()
    
    for pick_info in pickJson['data']:
        input_text.twitch_picker_avatar.set_value(pick_info['profile_image_url'])
    
    url = "https://www.twitch.tv/"+pick
    
    service.call("media_extractor", "play_media", entity_id=entity_id, media_content_id=url, media_content_type="video")
    
    # Bandaid for tvOS13 not updating status
    asyncio.sleep(5)
    state.set("media_player.man_cave", "playing")
    