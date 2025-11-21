import time
import asyncio
import random
import threading
from core import formatter
from core import tl
from curl_cffi import requests, AsyncSession

CHROME_VERSION = "124.0.0.0"
MAJOR_VERSION = "124"
USER_AGENT = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{CHROME_VERSION} Safari/537.36'

DEFAULT_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://kick.com/',
    'Origin': 'https://kick.com',
    'Connection': 'keep-alive',
    'User-Agent': USER_AGENT,
    'sec-ch-ua': f'"Chromium";v="{MAJOR_VERSION}", "Google Chrome";v="{MAJOR_VERSION}", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}

class ClaimManager:
    def __init__(self):
        self._reserved = set()
        self._claimed = set()
        self._lock = threading.Lock()
    def is_processed(self, reward_id):
        with self._lock:
            return reward_id in self._claimed
    def mark_claimed(self, reward_id, campaign_id):
        with self._lock:
            self._claimed.add(reward_id)
            self._reserved.discard(reward_id)
    def reserve(self, reward_id, campaign_id):
        with self._lock:
            if reward_id in self._claimed or reward_id in self._reserved:
                return False
            self._reserved.add(reward_id)
            return True
    def release_reservation(self, reward_id):
        with self._lock:
            self._reserved.discard(reward_id)

claim_manager = ClaimManager()

def get_proxy_or_none():
    proxy = tl.get_proxy()
    return proxy if proxy else None

def get_all_campaigns():
    headers = DEFAULT_HEADERS.copy()
    url = 'https://web.kick.com/api/v1/drops/campaigns'
    proxy = get_proxy_or_none()
    try:
        resp = requests.get(url, headers=headers, impersonate="chrome124", proxies=proxy, timeout=15)
        return resp.json()
    except Exception:
        return {}

def _is_reward_claimed_remote(cookies, reward_id, campaign_id):
    try:
        progress = get_drops_progress(cookies, max_attempts=1)
        if not progress:
            return None
        def walk(obj):
            if isinstance(obj, dict):
                if str(obj.get('id')) == str(reward_id) or str(obj.get('reward_id')) == str(reward_id):
                    return obj
                for v in obj.values():
                    res = walk(v)
                    if res: return res
            elif isinstance(obj, list):
                for item in obj:
                    res = walk(item)
                    if res: return res
            return None
        found = walk(progress)
        if found:
            if found.get('claimed') is True: return True
            if found.get('status') == 'claimed': return True
            return False
        return None
    except Exception:
        return None

def claim_drop_reward(reward_id, campaign_id, cookies, max_attempts=3):
    session_token = cookies.get("session_token")
    if not session_token:
        for k, v in cookies.items():
            if "session" in k and len(str(v)) > 20:
                session_token = v
                break
    
    if not session_token:
        return {'error': 'session_token missing'}

    reward_key = f"{reward_id}-{campaign_id}"
    if claim_manager.is_processed(reward_key):
        return None

    if _is_reward_claimed_remote(cookies, reward_id, campaign_id) is True:
        claim_manager.mark_claimed(reward_key, str(campaign_id))
        return {'message': 'Already claimed'}

    if not claim_manager.reserve(reward_key, str(campaign_id)):
        return None

    try:
        payload = {"reward_id": reward_id, "campaign_id": campaign_id}
        
        claim_headers = DEFAULT_HEADERS.copy()
        claim_headers.update({
            'Authorization': f'Bearer {session_token}',
            'X-Client-Token': 'e1393935a959b4020a4491574f6490129f678acdaa92760471263db43487f823', 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        base_wait = 2.0
        
        for attempt in range(max_attempts):
            proxy = get_proxy_or_none()
            try:
                resp = requests.post(
                    'https://web.kick.com/api/v1/drops/claim',
                    json=payload,
                    headers=claim_headers,
                    impersonate="chrome124",
                    proxies=proxy,
                    timeout=15
                )
                if resp.status_code == 200:
                    claim_manager.mark_claimed(reward_key, str(campaign_id))
                    return resp.json()
                if resp.status_code in (409, 410) or 'claimed' in resp.text.lower():
                    claim_manager.mark_claimed(reward_key, str(campaign_id))
                    return {'message': 'Already claimed'}
            except Exception:
                pass
            
            jitter = random.uniform(0.5, 2.0)
            time.sleep((base_wait * (attempt + 1)) + jitter)

        claim_manager.release_reservation(reward_key)
        return {'error': 'Failed to claim after retries'}
    except Exception as e:
        claim_manager.release_reservation(reward_key)
        return {'error': str(e)}

def get_drops_progress(cookies, max_attempts=3):
    session_token = cookies.get('session_token')
    if not session_token: return None
    
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Authorization': f'Bearer {session_token}',
        'X-Client-Token': 'e1393935a959b4020a4491574f6490129f678acdaa92760471263db43487f823'
    })

    for _ in range(max_attempts):
        proxy = get_proxy_or_none()
        try:
            resp = requests.get(
                'https://web.kick.com/api/v1/drops/progress',
                headers=headers,
                impersonate="chrome124",
                proxies=proxy,
                timeout=15
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        time.sleep(1 + random.random())
    return None

def get_random_stream_from_category(category_id, limit=15):
    url = f'https://web.kick.com/api/v1/livestreams?limit={limit}&sort=viewer_count_desc&category_id={category_id}'
    proxy = get_proxy_or_none()
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, impersonate="chrome124", proxies=proxy, timeout=15)
        data = response.json()
        
        livestreams = []
        if 'data' in data:
            if isinstance(data['data'], list):
                livestreams = data['data']
            elif isinstance(data['data'], dict):
                livestreams = data['data'].get('livestreams', [])
        
        if livestreams:
            max_idx = min(5, len(livestreams) - 1)
            idx = random.randint(0, max_idx)
            stream = livestreams[idx]
            channel = stream.get('channel') or stream
            return {
                'username': channel.get('slug') or channel.get('username'),
                'channel_id': channel.get('id')
            }
    except Exception as e:
        print(f"[Kick] Failed to get random stream: {e}")
    return {'username': None, 'channel_id': None}

async def get_stream_info(username):
    url = f'https://kick.com/api/v2/channels/{username}'
    result = {'is_live': False, 'game_id': None, 'game_name': None, 'live_stream_id': None}
    proxy = get_proxy_or_none()
    
    async with AsyncSession(impersonate="chrome124", proxies=proxy) as session:
        try:
            response = await session.get(url, headers=DEFAULT_HEADERS)
            if response.status_code == 200:
                data = response.json()
                livestream = data.get('livestream')
                if livestream:
                    result['is_live'] = True
                    result['live_stream_id'] = livestream.get('id')
                    categories = livestream.get('categories', [])
                    if categories:
                        result['game_id'] = categories[0].get('id')
                        result['game_name'] = categories[0].get('name')
        except Exception:
            pass
    return result

def get_channel_id(channel_name, cookies=None):
    proxy = get_proxy_or_none()
    try:
        s = requests.Session(impersonate="chrome124", proxies=proxy)
        if cookies:
            s.cookies.update(cookies)
        r = s.get(f"https://kick.com/api/v2/channels/{channel_name}", headers=DEFAULT_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("id")
    except Exception:
        pass
    return None

def get_token_with_cookies(cookies):
    session_token = cookies.get('session_token')
    if not session_token: return None
    
    headers = DEFAULT_HEADERS.copy()
    headers.update({
        'Authorization': f'Bearer {session_token}',
        'X-Client-Token': 'e1393935a959b4020a4491574f6490129f678acdaa92760471263db43487f823'
    })

    for _ in range(3):
        proxy = get_proxy_or_none()
        try:
            resp = requests.get(
                'https://websockets.kick.com/viewer/v1/token',
                headers=headers,
                impersonate="chrome124",
                proxies=proxy,
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json().get("data", {}).get("token")
        except Exception:
            pass
        time.sleep(2)
    return None

async def connection_channel(channel_id, username, category, token, preemption_callback=None):
    max_retries = 10
    retry_count = 0
    
    current_info = await get_stream_info(username)
    if not current_info['is_live']:
        return False

    watch_start_time = time.time()
    last_report_time = watch_start_time
    
    while retry_count < max_retries:
        try:
            proxy = get_proxy_or_none()
            async with AsyncSession(proxies=proxy, impersonate="chrome124", verify=True) as session:
                ws_url = f"wss://websockets.kick.com/viewer/v1/connect?token={token}"
                ws = await session.ws_connect(ws_url, headers=DEFAULT_HEADERS)
                
                retry_count = 0
                counter = 0
                await ws.send_json({"type": "channel_handshake", "data": {"message": {"channelId": channel_id}}})

                while True:
                    counter += 1
                    if counter % 2 == 0:
                        await ws.send_json({"type": "ping"})
                    
                    try:
                        _ = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    except asyncio.TimeoutError:
                        pass
                    
                    if preemption_callback and counter % 2 == 0:
                        should_switch = await preemption_callback(username)
                        if should_switch:
                            print(f"[Kick] Preempting {username} for higher priority target.")
                            await ws.close()
                            return True 

                    delay = 15 + random.uniform(1.5, 8.5)
                    
                    now = time.time()
                    if now - last_report_time >= (60 + random.uniform(-2, 2)):
                        formatter.update_streamer_progress(username, 60)
                        last_report_time = now
                        
                        check_info = await get_stream_info(username)
                        if not check_info['is_live']:
                            return True 
                        
                        if current_info.get('live_stream_id'):
                            await ws.send_json({
                                "type": "user_event",
                                "data": {
                                    "message": {
                                        "name": "tracking.user.watch.livestream",
                                        "channel_id": channel_id,
                                        "livestream_id": current_info['live_stream_id']
                                    }
                                }
                            })

                    await asyncio.sleep(delay)
                    
        except Exception:
            retry_count += 1
            await asyncio.sleep(5 + random.random())
            
    return False