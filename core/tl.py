import json
import os
import configparser
import shutil
import sys
import secrets

def get_run_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PROJECT_ROOT = get_run_dir()
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.ini")
EXAMPLE_CONFIG_PATH = os.path.join(PROJECT_ROOT, "example_config.ini")
LOCALES_DIR = os.path.join(PROJECT_ROOT, "locales")


def ensure_config():
    if not os.path.exists(CONFIG_PATH):
        if not os.path.exists(EXAMPLE_CONFIG_PATH):
            raise FileNotFoundError("example_config.ini not found in project root: " + EXAMPLE_CONFIG_PATH)
        shutil.copy(EXAMPLE_CONFIG_PATH, CONFIG_PATH)


def get_config():
    ensure_config()
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    return config


def save_config(config: configparser.ConfigParser):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        config.write(f)


def load_config_language():
    config = get_config()
    if "general" not in config or "language" not in config["general"]:
        return "en"
    return config["general"]["language"]


def load_translation(lang_code: str):
    path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if not os.path.exists(path):
        path = os.path.join(LOCALES_DIR, "en.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_proxy():
    config = get_config()
    proxy = config.get("network", "proxy", fallback=None)
    if proxy is None:
        return None
    proxy = str(proxy).strip()
    if not proxy:
        return None
    return {"http": proxy, "https": proxy, "ws": proxy, "wss": proxy, "socks5": proxy}


def ensure_webui_credentials():
    config = get_config()
    changed = False
    if "webui" not in config:
        config["webui"] = {}
        changed = True

    webui = config["webui"]
    password = webui.get("password", "").strip()
    secret_key = webui.get("secret_key", "").strip()
    regenerate_password = not password or password.lower() == "kick"
    regenerate_secret = not secret_key or secret_key.lower() == "stuxan"
    if regenerate_password:
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        password = "".join(secrets.choice(alphabet) for _ in range(16))
        webui["password"] = password
        changed = True
    if regenerate_secret:
        secret_key = secrets.token_hex(32)
        webui["secret_key"] = secret_key
        changed = True

    if changed:
        save_config(config)
        print(f"\n[KickDropMiner] Your WebUI password is: {password}\n", flush=True)
    return password, secret_key


ensure_config()
current_lang = load_config_language()
c = load_translation(current_lang)