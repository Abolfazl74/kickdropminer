import json
import os
import sys
import time
import concurrent.futures
from core import kick
from core import cookies_manager

def get_writable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_views_path():
    return os.path.join(get_writable_dir(), "current_views.json")

def get_priority_path():
    return os.path.join(get_writable_dir(), "priority.json")

def get_status_path():
    return os.path.join(get_writable_dir(), "farming_status.json")

def get_error_path():
    return os.path.join(get_writable_dir(), "error_status.json")

def get_stop_flag_path():
    return os.path.join(get_writable_dir(), "stop.flag")

def set_stop_signal():
    try:
        with open(get_stop_flag_path(), 'w') as f:
            f.write("STOP")
    except:
        pass

def clear_stop_signal():
    path = get_stop_flag_path()
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass

def should_stop():
    return os.path.exists(get_stop_flag_path())

def set_network_error(message=None):
    path = get_error_path()
    if message is None:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
        return

    data = {"error": str(message), "timestamp": time.time()}
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except:
        pass

def get_network_error():
    path = get_error_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if time.time() - data.get("timestamp", 0) > 30:
                return None
            return data.get("error")
    except:
        return None

def load_priority_list():
    path = get_priority_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def set_priority_user(username, enable=True):
    path = get_priority_path()
    current = load_priority_list()
    
    if enable:
        if username not in current:
            current.append(username)
    else:
        if username in current:
            current.remove(username)
            
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(current, f)
        return True
    except:
        return False

def save_farming_status(streamer=None, action="Idle"):
    path = get_status_path()
    data = {
        "streamer": streamer,
        "action": action
    }
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except:
        pass

def get_farming_status():
    path = get_status_path()
    if not os.path.exists(path):
        return {"streamer": None, "action": "Idle"}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"streamer": None, "action": "Idle"}

def validate_views_file():
    path = get_views_path()
    if not os.path.exists(path):
        return False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content: return False
            data = json.loads(content)
            if 'data' not in data: return False
            return True
    except Exception:
        return False

def force_reset_views():
    path = get_views_path()
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except:
            pass
    return False

def collect_usernames(json_filename='current_views.json'):
    cookies = cookies_manager.load_cookies("cookies.txt")
    priority_list = load_priority_list()
    
    all_campaigns = {"data": []}
    user_progress = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_campaigns = executor.submit(kick.get_all_campaigns)
        future_progress = None
        if cookies:
            future_progress = executor.submit(kick.get_drops_progress, cookies)
            
        try:
            all_campaigns = future_campaigns.result(timeout=6) or {"data": []}
        except Exception:
            pass 
            
        if future_progress:
            try:
                prog_resp = future_progress.result(timeout=6) or {"data": []}
                for c in prog_resp.get('data', []):
                    for r in c.get('rewards', []):
                        rid = str(r.get('id'))
                        user_progress[rid] = r
            except Exception:
                pass

    result = []
    
    for campaign in all_campaigns.get('data', []):
        campaign_id = campaign.get('id')
        cat_obj = campaign.get('category', {})
        category_id = cat_obj.get('id')
        category_name = cat_obj.get('name', 'Unknown')
        image_url = cat_obj.get('banner_url') or cat_obj.get('image_url') or campaign.get('image_url')
        
        channels = campaign.get('channels', [])
        streamer_list = []
        if channels:
            streamer_list = [ch.get('slug') for ch in channels if ch.get('slug')]
        
        is_general = len(streamer_list) == 0
        
        for reward in campaign.get('rewards', []):
            rid = str(reward.get('id'))
            if not rid: continue
            
            u_data = user_progress.get(rid, {})
            current_progress = u_data.get('progress', 0)
            is_claimed = u_data.get('claimed', False)
            
            req_units = reward.get('required_units', 0)
            remaining_units = req_units * (1.0 - current_progress)
            
            has_priority_streamer = False
            for u in streamer_list:
                if u in priority_list:
                    has_priority_streamer = True
                    break

            s = {
                'usernames': streamer_list if not is_general else ["Any Streamer"],
                'drop_name': reward.get('name') or 'Unknown Reward',
                'progress': current_progress,
                'claimed': is_claimed,
                'required_seconds': int(remaining_units * 60),
                'category_name': category_name,
                'category_id': category_id,
                'image_url': image_url,
                'reward_id': rid,
                'campaign_id': campaign_id,
                'type': 2 if is_general else 1,
                'is_priority': has_priority_streamer
            }
            result.append(s)

    return result

def update_streamer_progress(username, watched_seconds):
    pass