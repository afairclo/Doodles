@service
def twitch_picker(target=None, pick=None):
    import json
    import requests
    import random
    import urllib.parse
    import asyncio
    
    state.set("automation.man_cave_idle","on")
    if target == None:
        target = "media_player.man_cave"
    
    # Twitch OAuth
    requestHeaders = {
        'Authorization':'Bearer ' + input_text.twitch_oauth_token,
        'Client-Id':str(input_text.twitch_client_id)
        }
    
    # Recovery in event of stream failure
    # last_streamer = "https://api.twitch.tv/helix/streams?user_login="+input_text.twitch_picker
    # response = task.executor(requests.get, last_streamer, headers=requestHeaders)
    # streams = response.json()
    # if len(streams['data']) != 0:
    #    pick = input_text.twitch_picker
    
    skipList = [
                input_text.twitch_picker,
                'presscorps',
                'bf2tv',
                'saltybet',
                'rlgym',
                'xfearxireaper',
                'virtualjapan',
                'tomixbf2',
                'PS2CPC',
                'jynxzi',
                'kaicenat'
                ]
                
    nostalgiaGames = [
                'Foxhole',
                'HELLDIVERS™ 2',
                'PlanetSide 2',
                'Natural Selection 2',
                'Battlefield 2', # Like sequels much?
                'Battlefield 2142',
                'Deep Rock Galactic',
                'Supreme Commander: Forged Alliance'
                ]
                
    nostalgiaPick = random.choice(nostalgiaGames)
        
    if pick == None:
    
        streamers = []
        # Get top stream. If they have over 225k viewers, stream it.
        topStream = ""
        requestURL = "https://api.twitch.tv/helix/streams?language=en&first=1"
        response = task.executor(requests.get, requestURL, headers=requestHeaders)
        streams = response.json()
        for stream in streams['data']:
            if stream['user_login'] not in skipList:
                if stream['viewer_count'] >= 200000:
                    pick = stream['user_login']
                    specialStream = True
                else:
                    topStream = stream['user_login']
                    specialStream = False
            else:
                specialStream = False
            
    # Get followed channels, if any are online, pick one at random and stream it. 100 max at this time.
    
    # Deprecated 
    
    #followedOnline = []
    #onlineCheckURL = "https://api.twitch.tv/helix/streams?type=live&first=100"
    
    #requestURL = "https://api.twitch.tv/helix/users/follows?from_id="+input_text.twitch_userid+"&first=100"
    #response = task.executor(requests.get, requestURL, headers=requestHeaders)
    #followedChannels = response.json()
    #for channel in followedChannels['data']:
    #    onlineCheckURL = onlineCheckURL+"&user_login="+channel['to_login']
    #response = task.executor(requests.get, onlineCheckURL, headers=requestHeaders)
    #followedOnlineChannels = response.json()
    #for channel in followedOnlineChannels['data']:
    #    followedOnline.append(channel['user_login'])
    #if input_text.twitch_picker.lower() in followedOnline:
    #    followedOnline.remove(input_text.twitch_picker.lower())
    #if len(followedOnline) > 0:
    #    pick = random.choice(followedOnline)
        
    # Build list of game IDs
    
    if pick == None:
        
        # Games that must be in the running
        
        gameIDs = [
            '1331855755', # Darts
            ]
        
        # Append trending games
        chartGames = [
            sensor.steam_charts_top_trending_game,
            sensor.steam250_week_top_30,
            ]

        # Skip trending games not interested in
        skipGames = [
            'Apex Legends',
            'Call of Duty: Warzone',
            'Counter-Strike',
            'Dead by Daylight',
            'Dota 2',
            'EA Sports FC 24',
            'Fortnite',
            'Grand Theft Auto V',
            "I'm Only Sleeping",
            'IRL',
            'Just Chatting',
            'League of Legends',
            'Minecraft',
            'Music',
            'Nothing',
            'Overwatch 2',
            'Portal 2',
            'Rust',
            'Satisfactory',
            'Slots',
            'Sports',
            'Street Fighter 6',
            'Teamfight Tactics',
            "Tom Clancy's Rainbow Six Siege",
            'Trackmania',
            'VALORANT',
            'Vampire Survivors',
            'Virtual Casino',
            'World of Warcraft'
            ]
            
        # Append Steam friends games
        # Use steamID64 value
        
        steamUsers = [
            '76561197961521763', # FapFlop
            '76561197990038627', # Bread86
            '76561198037335714', # K8ers
            '76561198140759821', # Yen
            '76561197970285821', # n0m3rcy
            '76561198112594074' # Drizzle
            ]
        
        for user in steamUsers:
            requestURL = "http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key="+input_text.steamapi+"&format=json&steamid="+user
            response = task.executor(requests.get, requestURL, headers=requestHeaders)
            steamJson = response.json()
            if 'games' in steamJson['response']:
                for game in steamJson['response']['games']:
                    if game['playtime_2weeks'] > 120 and game['name'] not in skipGames:
                        chartGames.append(game['name'])
            
        # Append top 5 games on Twitch that aren't in skipGames
        topTwitch = []
        requestURL = "https://api.twitch.tv/helix/games/top?first=20"
        response = task.executor(requests.get, requestURL, headers=requestHeaders)
        top5Json = response.json()
        for game in top5Json['data']:
            if game['name'] not in skipGames:
                topTwitch.append(game['name'])
        topTwitch = topTwitch[:5]
        chartGames.extend(topTwitch)
        
        chartGames.append(nostalgiaPick)
        
        # Remove duplicates to reduce calls
        chartGames = list(set(chartGames))
        
        for chartGame in chartGames:
            if chartGame not in skipGames:
                requestURL = "https://api.twitch.tv/helix/games?name="+urllib.parse.quote(chartGame)
                response = task.executor(requests.get, requestURL, headers=requestHeaders)
                trendingJson = response.json()
                for trendingGame in trendingJson['data']:
                    gameIDs.append(trendingGame['id'])
        
        # Remove duplicates to reduce favoritism
        gameIDs = list(set(gameIDs))
        
        # No repeats.
        if input_text.twitch_picker_gameID in gameIDs:
            gameIDs.remove(input_text.twitch_picker_gameID)
        
        # Pick loop
        input_number.twitch_picker_loops.set_value(0)
        loops = 0
        while len(streamers) == 0:
            loops += 1
            input_number.twitch_picker_loops.set_value(loops)
            # Pick a game
            chosenGame = random.choice(gameIDs)
            # Debug
            #chosenGame = "493388"

            # Get stream candidates, top 10 streamers for chosen game
            requestURL = "https://api.twitch.tv/helix/streams?game_id="+chosenGame+"&first=10"
            response = task.executor(requests.get, requestURL, headers=requestHeaders)
            streams = response.json()
            # Sum viewer count across all streams
            totalViewers = 0
            for stream in streams['data']:
                totalViewers += stream['viewer_count']
            for stream in streams['data']:
                # If game is popping of from single English stream, pick it
                # If it's a single non-English stream, skip game
                if (stream['viewer_count'] / totalViewers)>0.5:
                    if stream['language'] == "en":
                        specialStream = True
                        streamers.append(stream['user_login'])
                        pick = stream['user_login']
                else:
                    if stream['user_login'] not in skipList and stream['language'] == "en":
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
        
        if pick == None:
        
            # Add top streamer if the stream isn't rare.
            if len(streamers) > 5 and topStream:
                streamers.append(topStream)
        
            pick = random.choice(streamers)
            
            if pick == topStream:
                specialStream = True
    
    # Get stream info
    
    pickURL = "https://api.twitch.tv/helix/streams?user_login="+pick
    response = task.executor(requests.get, pickURL, headers=requestHeaders)
    pickJson = response.json()
    
    for pick_info in pickJson['data']:
        input_text.twitch_picker.set_value(pick_info['user_name'])
        input_text.twitch_picker_game.set_value(pick_info['game_name'])
        input_text.twitch_picker_gameID.set_value(pick_info['game_id'])
        if specialStream == True:
            input_text.twitch_picker_title.set_value(pick_info['title']+" 🔴 "+str(pick_info['viewer_count'])+" 💫")
        else:
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
            
    # Stop current media
    service.call("media_player", "media_stop", entity_id=target)
    asyncio.sleep(2)
    # Send stream to target
    service.call("media_extractor", "play_media", entity_id=target, media_content_id=url, media_content_type="video")
    
    # Bandaid for tvOS not updating status
    asyncio.sleep(5)
    state.set("media_player.man_cave", "playing")
    