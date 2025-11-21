import json
import os
import sys
from core import tl
from core import kick
from core import cookies_manager

def get_writable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def sync_drops_data(server_data, cookies, filepath="current_views.json"):
    views_path = os.path.join(get_writable_dir(), filepath)
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            local_data = json.load(f)
        server_campaigns = server_data.get('data', [])
        updated_data = local_data
        if 'data' in updated_data and 'planned' in updated_data['data']:
            for item in updated_data['data']['planned']:
                campaign_id = item.get('category_id')
                usernames = item.get('usernames', [])
                item_id = item.get('id')
                item_type = item.get('type', 1)
                for campaign in server_campaigns:
                    if str(campaign.get('category', {}).get('id')) == str(campaign_id):
                        for reward in campaign.get('rewards', []):
                            remote_id = reward.get('id')
                            remote_progress = reward.get('progress', 0)
                            remote_claimed = reward.get('claimed', False)
                            required_units = reward.get('required_units', 0)
                            if str(remote_id) == str(item_id):
                                item['claim'] = 1 if remote_claimed else 0
                                remaining_units = required_units * (1 - remote_progress)
                                item['required_units'] = max(0, int(remaining_units))
        with open(views_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print("[Stuxan] sync_drops_data FAILED:", e)
        return False

def convert_drops_json(drops_data):
    result = {
        "data": {
            "planned": [],
            "finished": []
        }
    }
    if 'data' not in drops_data:
        return result
    for campaign in drops_data['data']:
        category_id = campaign.get('category', {}).get('id')
        if category_id is None:
            continue
        channels = campaign.get('channels', [])
        if not channels:
            rewards = campaign.get('rewards', [])
            for reward in rewards:
                reward_id = reward.get('id')
                required_units = reward.get('required_units', 0)
                planned_item = {
                    "category_id": category_id,
                    "type": 2,
                    "claim": 0,
                    "required_units": required_units,
                    "id": reward_id
                }
                result['data']['planned'].append(planned_item)
        else:
            usernames = [channel.get('slug') for channel in channels if channel.get('slug')]
            total_required_units = sum(r.get('required_units', 0) for r in campaign.get('rewards', []))
            reward_id = campaign.get('rewards', [{}])[0].get('id')
            planned_item = {
                "category_id": category_id,
                "type": 1,
                "claim": 0,
                "usernames": usernames,
                "required_units": total_required_units,
                "id": reward_id
            }
            result['data']['planned'].append(planned_item)
    views_path = os.path.join(get_writable_dir(), "current_views.json")
    with open(views_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    return result

def collect_usernames(json_filename='current_views.json'):
    views_path = os.path.join(get_writable_dir(), json_filename)
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return []
            data = json.loads(content)
    except Exception:
        return []
    streamers_data = []
    for item in data.get('data', {}).get('planned', []):
        if 'usernames' in item:
            required_seconds = item.get('required_units', 0) * 60
            claim_status = item.get('claim')
            for username in item['usernames']:
                streamers_data.append({
                    'username': username,
                    'required_seconds': required_seconds,
                    'claim': claim_status
                })
    return streamers_data

def collect_targeted_streamers(json_filename='current_views.json'):
    cookies = cookies_manager.load_cookies("cookies.txt")
    server_data = {"data": []}
    if cookies:
        try:
            server_data = kick.get_drops_progress(cookies) or {"data": []}
        except:
            pass

    views_path = os.path.join(get_writable_dir(), json_filename)
    reward_to_usernames = {}

    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                data = json.loads(content)
                for item in data.get('data', {}).get('planned', []):
                    reward_id = item.get('id')
                    if reward_id and item.get('usernames'):
                        reward_to_usernames[str(reward_id)] = item['usernames']
    except:
        pass

    result = []
    for campaign in server_data.get('data', []):
        campaign_id = campaign.get('id') or campaign.get('category', {}).get('id')
        category_name = campaign.get('category', {}).get('name', '')

        for reward in campaign.get('rewards', []):
            rid = reward.get('id') or reward.get('reward_id')
            if not rid:
                continue

            key = str(rid)
            usernames = reward_to_usernames.get(key, [])

            s = {
                'usernames': usernames,
                'drop_name': reward.get('name') or '',
                'progress': reward.get('progress'),
                'claimed': reward.get('claimed', False),
                'required_seconds': reward.get('required_seconds', 0),
                'claim': 1 if reward.get('claimed') else 0,
                'category_name': category_name,
                'reward_id': rid,
                'campaign_id': campaign_id,
            }
            result.append(s)

    return result
    

def update_streamer_progress(username, watched_seconds, json_filename='current_views.json', update_type=1):
    watched_minutes = round(watched_seconds / 60.0, 1)
    views_path = os.path.join(get_writable_dir(), json_filename)
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data['data']['planned']:
            if update_type == 2 and item.get('type') == 2:
                current_units = round(float(item.get('required_units', 0)), 1)
                new_units = round(max(0.0, current_units - watched_minutes), 1)
                item['required_units'] = new_units
                with open(views_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            elif update_type == 1 and item.get('type') == 1 and 'usernames' in item and username in item['usernames']:
                current_units = round(float(item.get('required_units', 0)), 1)
                new_units = round(max(0.0, current_units - watched_minutes), 1)
                item['required_units'] = new_units
                with open(views_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
        if update_type == 1:
            return update_streamer_progress(username, watched_seconds, json_filename, update_type=2)
        return False
    except Exception:
        return False

async def get_remaining_time(username=None, json_filename='current_views.json', get_type=1):
    views_path = os.path.join(get_writable_dir(), json_filename)
    try:
        with open(views_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data['data']['planned']:
            if get_type == 2 and item.get('type') == 2:
                remaining_minutes = item.get('required_units', 0)
                return int(remaining_minutes * 60)
            elif get_type == 1 and item.get('type') == 1 and 'usernames' in item and username in item['usernames']:
                remaining_minutes = item.get('required_units', 0)
                return int(remaining_minutes * 60)
        if get_type == 1:
            return await get_remaining_time(username, json_filename, get_type=2)
        return 0
    except Exception:
        return 0
    
def load_views():
    views_path = os.path.join(get_writable_dir(), "current_views.json")
    if not os.path.exists(views_path):
        return None
    with open(views_path, 'r', encoding='utf-8') as f:
        return json.load(f)