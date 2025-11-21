import threading
import subprocess
import time
import sys
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
from webui.logpipe import get_ui_logs
from core import kick
from core import tl
from core import cookies_manager
from core import formatter

app = Flask(__name__, template_folder="templates", static_folder="static")

PANEL_PASSWORD, SECRET_KEY = tl.ensure_webui_credentials()
app.secret_key = SECRET_KEY

LOG_LINES = 300
farmer_process = None
farmer_logs = []
farmer_lock = threading.Lock()

selected_game_id = None
selected_drop_type = "auto"
LOGIN_PASSWORD = PANEL_PASSWORD

def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def check_cookies_exist():
    cookie_path = os.path.join(get_project_root(), "cookies.txt")
    return os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0

def get_games():
    sys.path.insert(0, get_project_root())
    campaigns_resp = kick.get_all_campaigns() or {}
    seen = set()
    games = []
    for camp in campaigns_resp.get("data", []):
        cat = camp.get("category", {})
        cat_id = str(cat.get("id"))
        if not cat_id or cat_id in seen:
            continue
        image = cat.get("icon") or "/static/default_game.png"
        games.append({"id": cat_id, "name": cat.get("name", "Unknown"), "image": image})
        seen.add(cat_id)
    return games

def start_farmer(game_id):
    global farmer_process, farmer_logs
    
    if not check_cookies_exist():
        with farmer_lock:
            farmer_logs.append("ERROR: No cookies found. Please import cookies first.")
        return False

    if not formatter.validate_views_file():
        with farmer_lock:
            farmer_logs.append("WARNING: Refreshing drop configuration...")
        formatter.force_reset_views()

    with farmer_lock:
        farmer_logs.clear()

        if getattr(sys, "frozen", False):
            import farmer
            def runner():
                for line in ["Smart Farmer starting..."]:
                    farmer_logs.append(line)
                try:
                    farmer.main(
                        game_id,
                        "auto",
                        log_callback=lambda msg: farmer_logs.append(msg)
                    )
                except Exception as e:
                    farmer_logs.append(f"Farmer Error: {e}")
            threading.Thread(target=runner, daemon=True).start()
            farmer_process = None
            return

        if farmer_process and farmer_process.poll() is None:
            farmer_process.terminate()
            time.sleep(1)

        if getattr(sys, 'frozen', False):
            script_path = os.path.join(sys._MEIPASS, "farmer.py")
        else:
            script_path = os.path.join(get_project_root(), "farmer.py")

        cmd = [sys.executable, script_path, "--category", str(game_id), "--mode", "auto"]
        cwd = get_project_root()

        env = {**os.environ, "PYTHONUNBUFFERED": "1"}

        try:
            farmer_process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )
        except Exception as e:
            farmer_logs.append(f"Failed to spawn process: {e}")
            return False

        def log_reader():
            while True:
                line = farmer_process.stdout.readline()
                if not line and farmer_process.poll() is not None:
                    break
                if line:
                    farmer_logs.append(line.rstrip("\r\n"))
                    if len(farmer_logs) > LOG_LINES:
                        farmer_logs.pop(0)

        threading.Thread(target=log_reader, daemon=True).start()
        return True

@app.route("/login", methods=["GET", "POST"])
def login():
    err = None
    if request.method == "POST":
        password = request.form.get("password")
        if password == LOGIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("main_page"))
        else:
            err = tl.c.get("wrong_password", "Wrong password!")
    return render_template("login.html", error=err, t=tl.c)

@app.route("/logout")
@login_required
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET"])
@login_required
def main_page():
    global selected_game_id
    games = get_games()
    has_cookies = check_cookies_exist()

    if has_cookies:
        if not selected_game_id and games:
            selected_game_id = games[0]["id"]
        
        if selected_game_id:
            if farmer_process is None or farmer_process.poll() is not None:
                 start_farmer(selected_game_id)
    
    return render_template("index.html",
                           games=games,
                           current_game_id=selected_game_id,
                           has_cookies=has_cookies,
                           t=tl.c)

@app.route("/api/select", methods=["POST"])
@login_required
def select():
    global selected_game_id
    data = request.get_json(force=True)
    game_id = data.get("game_id")
    if game_id:
        selected_game_id = game_id
    
    success = start_farmer(selected_game_id)
    return jsonify({"ok": success})

@app.route("/api/logs")
def api_logs():
    return {"logs": get_ui_logs()}

@app.route("/api/status")
@login_required
def api_status():
    has_cookies = check_cookies_exist()
    if has_cookies:
        streamers = formatter.collect_usernames()
        current_status = formatter.get_farming_status()
        farmer = {
            "status": "RUNNING" if farmer_process and farmer_process.poll() is None else "STOPPED",
            "logs": farmer_logs[-50:],
            "current_streamer": current_status.get("streamer"),
            "current_action": current_status.get("action")
        }
        priorities = formatter.load_priority_list()
    else:
        streamers = []
        farmer = {"status": "AUTH_REQUIRED", "logs": ["Waiting for login..."], "current_streamer": None}
        priorities = []

    return jsonify({
        'authenticated': has_cookies,
        'progress': {"data": []}, 
        'streamers': streamers, 
        'farmer': farmer,
        'priorities': priorities
    })

@app.route("/api/claim", methods=["POST"])
@login_required
def api_claim():
    data = request.get_json(force=True) or {}
    reward_id = data.get('reward_id')
    campaign_id = data.get('campaign_id')
    cookies = cookies_manager.load_cookies("cookies.txt") or {}
    if not reward_id or not campaign_id:
        return jsonify({'error': 'missing parameters'}), 400
    result = kick.claim_drop_reward(reward_id, campaign_id, cookies)
    if result is None or (isinstance(result, dict) and result.get('error')):
        return jsonify({'result': result, 'error': 'Failed to claim'}), 500
    return jsonify({'result': result})

@app.route("/api/set_priority", methods=["POST"])
@login_required
def set_priority():
    data = request.get_json(force=True) or {}
    username = data.get('username')
    enable = data.get('enable', True)
    if not username:
        return jsonify({'error': 'missing username'}), 400
    success = formatter.set_priority_user(username, enable)
    return jsonify({'ok': success})

@app.route("/api/stop_farmer", methods=["POST"])
@login_required
def stop_farmer():
    global farmer_process
    with farmer_lock:
        if farmer_process and farmer_process.poll() is None:
            farmer_process.terminate()
            time.sleep(0.5)
            return jsonify({"ok": True, "status": "STOPPED"})
    return jsonify({"ok": True, "status": "NOT_RUNNING"})

@app.route("/api/save_cookies", methods=["POST"])
@login_required
def save_cookies():
    data = request.get_json(force=True)
    raw_content = data.get("content", "").strip()
    if not raw_content:
        return jsonify({"ok": False, "error": "Empty content"})

    target_path = os.path.join(get_project_root(), "cookies.txt")
    
    if "\t" in raw_content and ".kick.com" in raw_content:
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_content)
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)})

    if len(raw_content) > 20 and "\n" not in raw_content and "{" not in raw_content:
        netscape_content = f".kick.com\tTRUE\t/\tTRUE\t2147483647\tsession_token\t{raw_content}\n"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(netscape_content)
        return jsonify({"ok": True})

    if raw_content.startswith("[") or raw_content.startswith("{"):
        try:
            json_cookies = json.loads(raw_content)
            if isinstance(json_cookies, dict):
                json_cookies = [json_cookies] 
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for c in json_cookies:
                    domain = c.get("domain", ".kick.com")
                    if not domain.startswith("."): domain = "." + domain
                    path = c.get("path", "/")
                    secure = str(c.get("secure", True)).upper()
                    expiry = int(c.get("expirationDate", time.time() + 31536000))
                    name = c.get("name")
                    value = c.get("value")
                    if name and value:
                        f.write(f"{domain}\tTRUE\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": "Invalid JSON format"})

    return jsonify({"ok": False, "error": "Unrecognized cookie format"})

@app.route("/api/reset_config", methods=["POST"])
@login_required
def reset_config():
    success = formatter.force_reset_views()
    global selected_game_id
    if selected_game_id:
        start_farmer(selected_game_id)
    return jsonify({"ok": success})

if __name__ == "__main__":
    frozen = getattr(sys, "frozen", False)
    app.run(debug=False, host="0.0.0.0", port=8080, use_reloader=not frozen)