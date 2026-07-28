import os
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
ERROR_LOG = os.path.join(BASE_DIR, "error.log")

logging.basicConfig(
    filename=ERROR_LOG,
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_telegram_token():
    return load_config().get("telegram_token", "")

def get_admin_chat_id():
    return load_config().get("admin_chat_id", None)

def get_ban_list():
    return load_config().get("ban_list", [])

def get_vip_list():
    return load_config().get("vip_list", [])

def add_ban(user_id):
    cfg = load_config()
    if user_id not in cfg.get("ban_list", []):
        cfg.setdefault("ban_list", []).append(user_id)
        save_config(cfg)

def remove_ban(user_id):
    cfg = load_config()
    if user_id in cfg.get("ban_list", []):
        cfg["ban_list"].remove(user_id)
        save_config(cfg)

def add_vip(user_id):
    cfg = load_config()
    if user_id not in cfg.get("vip_list", []):
        cfg.setdefault("vip_list", []).append(user_id)
        save_config(cfg)

def remove_vip(user_id):
    cfg = load_config()
    if user_id in cfg.get("vip_list", []):
        cfg["vip_list"].remove(user_id)
        save_config(cfg)

def is_banned(user_id):
    return user_id in get_ban_list()

def is_vip(user_id):
    return user_id in get_vip_list()