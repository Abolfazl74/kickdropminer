import asyncio
import random
import time
from core import kick
from core import formatter

async def watch_streamer(username, category_id, duration=60, log_callback=None):
    if formatter.should_stop(): return False

    if log_callback:
        log_callback(f"Checking live status: {username}...")
        
    import core.cookies_manager as cm
    cookies = cm.load_cookies("cookies.txt")
    token = kick.get_token_with_cookies(cookies)
    
    if not token:
        if log_callback: log_callback("Failed to get access token.")
        return False

    stream_info = await kick.get_stream_info(username)
    if not stream_info['is_live']:
        return False

    channel_id = kick.get_channel_id(username, cookies)
    if not channel_id:
        return False

    if log_callback:
        log_callback(f" >> Farming {username} for drops...")

    formatter.save_farming_status(username, "Farming")

    async def check_higher_priority(current_user):
        if formatter.should_stop(): return True

        priorities = formatter.load_priority_list()
        if current_user in priorities: return False
        if not priorities: return False
            
        all_drops = formatter.collect_usernames()
        for p_user in priorities:
            user_has_drop = False
            for drop in all_drops:
                if str(drop['category_id']) == str(category_id) and not drop['claimed']:
                    if p_user in drop.get('usernames', []):
                        user_has_drop = True
                        break
            if user_has_drop:
                info = await kick.get_stream_info(p_user)
                if info['is_live']:
                    if log_callback: log_callback(f"!! Interrupting: Priority streamer {p_user} is LIVE.")
                    return True
        return False

    try:
        await kick.connection_channel(channel_id, username, category_id, token, preemption_callback=check_higher_priority)
    finally:
        formatter.save_farming_status(None, "Idle")
        
    return True

async def smart_farm_loop(category_id, log_callback=None):
    formatter.clear_stop_signal()

    while True:
        if formatter.should_stop():
            if log_callback: log_callback("Farmer stopped by user signal.")
            break

        if log_callback: log_callback("Scanning active drops...")
        formatter.save_farming_status(None, "Scanning")
        
        all_drops = formatter.collect_usernames()
        priority_list = formatter.load_priority_list()
        
        active = [
            d for d in all_drops 
            if (str(d['category_id']) == str(category_id) or str(d['campaign_id']) == str(category_id))
            and not d['claimed']
            and d['progress'] < 1.0
        ]

        if not active:
            if log_callback: log_callback("No active drops found. Sleeping 60s...")
            formatter.save_farming_status(None, "Waiting")
            
            for _ in range(30): 
                if formatter.should_stop(): return
                await asyncio.sleep(2)
            continue

        active.sort(key=lambda x: (
            not any(u in priority_list for u in x.get('usernames', [])),
            x['type'] == 2,        
            -x['progress']         
        ))

        farmed_successfully = False

        for drop in active:
            if formatter.should_stop(): break

            usernames = drop.get('usernames', [])
            is_general = drop['type'] == 2 or "Any Streamer" in usernames
            
            if not is_general:
                usernames.sort(key=lambda u: u not in priority_list)
                for u in usernames:
                    if formatter.should_stop(): break
                    if await watch_streamer(u, category_id, log_callback=log_callback):
                        farmed_successfully = True
                        break
                if farmed_successfully: break
            
            else:
                target_found = False
                for p_user in priority_list:
                    if formatter.should_stop(): break
                    info = await kick.get_stream_info(p_user)
                    if info['is_live'] and str(info['game_id']) == str(category_id):
                        if await watch_streamer(p_user, category_id, log_callback=log_callback):
                            farmed_successfully = True
                            target_found = True
                            break
                
                if not target_found:
                    if log_callback: log_callback("No priority streamers live. Finding random...")
                    random_stream = kick.get_random_stream_from_category(category_id)
                    if random_stream.get('username'):
                        if await watch_streamer(random_stream['username'], category_id, log_callback=log_callback):
                            farmed_successfully = True
                            break
                else:
                    break 

        if formatter.should_stop(): break

        if not farmed_successfully:
            if log_callback: log_callback("No suitable live streamers found. Waiting...")
            formatter.save_farming_status(None, "Waiting")
            for _ in range(15):
                if formatter.should_stop(): return
                await asyncio.sleep(2)
        
        await asyncio.sleep(2)

async def run_farming(mode, category_id, log_callback=None):
    if log_callback:
        log_callback(f"Starting Smart Farmer for Category {category_id}")
    await smart_farm_loop(category_id, log_callback)