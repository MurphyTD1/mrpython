import time
import json
import uuid
import re
import random
import threading
import itertools
import requests
import urllib.parse
import os
from config import logging
from proxy_manager import load_local_proxies, save_local_proxies

# ---------- FreeLLM ----------
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "cookie.txt")
DEFAULT_COOKIE = "NEXT_LOCALE=en; __Host-next-auth.csrf-token=a5577b41fc2a321176bedbd97790d4bdc520efef81c1817e6d67530cce04d963%7Cdf4f6439bf1b83a2f8ade382dd89c9e80b1b61a125292fabf043295e8c899f8d; __Secure-next-auth.callback-url=https%3A%2F%2Fapifreellm.com"

def get_cookie():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookie = f.read().strip()
            if cookie:
                return cookie
    return DEFAULT_COOKIE

FREELLM_COOKIE = get_cookie()
FREELLM_URL = "https://apifreellm.com/api/chatAPI"
FREELLM_HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://apifreellm.com",
    "referer": "https://apifreellm.com/en",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": FREELLM_COOKIE
}

# ---------- DeepAI ----------
DEEPAI_API_KEY = "tryit-86002831590-99ba3a9b2ad218c56cd5436328d2d08d"
DEEPAI_CHAT_URL = "https://api.deepai.org/hacking_is_a_serious_crime"

# ---------- ChatAI ----------
CHATAI_URL = "https://chatai.org/api/chat"
CHATAI_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://chatai.org",
    "Referer": "https://chatai.org/chat",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ---------- MODELS ----------
MODELS = {
    "1":  {"name": "ChatGPT",          "source": "chatai", "model_id": "openai/gpt-4o-mini",      "desc": "Dengeli"},
    "2":  {"name": "GPT-OSS 120B",     "source": "deepai", "model_id": "gpt-oss-120b",            "desc": "Akıl Yürütme"},
    "3":  {"name": "GPT-5 Nano",       "source": "deepai", "model_id": "gpt-5-nano",              "desc": "Pratik"},
    "4":  {"name": "DeepSeek V3",      "source": "deepai", "model_id": "deepseek-v3.2",           "desc": "Kodlama"},
    "5":  {"name": "Claude Haiku",     "source": "chatai", "model_id": "anthropic/claude-haiku-4-5", "desc": "Yazar"},
    "6":  {"name": "Perplexity",       "source": "chatai", "model_id": "perplexity/sonar",        "desc": "Araştırma"},
    "7":  {"name": "Gemini 2.5 Flash", "source": "deepai", "model_id": "gemini-2.5-flash-lite",   "desc": "Hız"},
    "8":  {"name": "Llama 4 Scout",    "source": "deepai", "model_id": "llama-4-scout",           "desc": "Bağlam"},
    "9":  {"name": "Qwen 72B",         "source": "chatai", "model_id": "qwen/qwen-2.5-72b-instruct", "desc": "Çeviri"},
    "10": {"name": "Gemma 4",          "source": "deepai", "model_id": "gemma-4",                 "desc": "Verimli"},
    "11": {"name": "FreeLLM",          "source": "chatai", "model_id": None,                      "desc": ""},
    "12": {"name": "WormGPT",          "source": "wormgpt","model_id": "deepseek-v3.2",           "desc": ""},
}

# ---------- CHAT FONKSİYONLARI ----------
def chat_freellm(user_input, history):
    history.append({"role": "user", "content": user_input})
    payload = {"inputCode": history[-20:]}
    try:
        response = requests.post(FREELLM_URL, headers=FREELLM_HEADERS, json=payload, timeout=(10, 120))
        if response.status_code == 429:
            time.sleep(1.5)
            return chat_freellm(user_input, history[:-1])
        if response.status_code != 200:
            return None
        raw = response.text.strip()
        if not raw:
            return None
        history.append({"role": "assistant", "content": raw})
        return raw
    except Exception as e:
        logging.error(f"FreeLLM hatası: {e}")
        return None

def chat_deepai(user_input, history, model_id, system_prompt=None):
    clean_history = history[-20:] if len(history) > 20 else history
    history.append({"role": "user", "content": user_input})
    
    messages = []
    if system_prompt:
        messages.append({"role": "user", "content": system_prompt})
    messages.extend(clean_history)
    messages.append({"role": "user", "content": user_input})
    
    chat_history_json = json.dumps(messages, ensure_ascii=False)
    boundary = "----WebKitFormBoundary" + ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_style"\r\n\r\nchat\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chatHistory"\r\n\r\n{chat_history_json}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n{model_id}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="session_uuid"\r\n\r\n{str(uuid.uuid4())}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="sensitivity_request_id"\r\n\r\n{str(uuid.uuid4())}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="hacker_is_stinky"\r\n\r\nvery_stinky\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="enabled_tools"\r\n\r\n["image_generator","image_editor"]\r\n'
        f"--{boundary}--\r\n"
    )
    headers = {
        "api-key": DEEPAI_API_KEY,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Origin": "https://deepai.org",
        "Referer": "https://deepai.org/chat",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.post(DEEPAI_CHAT_URL, headers=headers, data=body, timeout=(10, 120))
        if response.status_code != 200:
            return None
        raw = response.text.strip()
        if not raw:
            return None
        raw = re.sub(r'\x1dTHINKING_START.*?\x1dTHINKING_END', '', raw, flags=re.DOTALL)
        raw = raw.strip()
        history.append({"role": "assistant", "content": raw})
        return raw
    except Exception as e:
        logging.error(f"DeepAI hatası: {e}")
        return None

def parse_chatai_response(response, history):
    content_type = response.headers.get("content-type", "")
    full_text = ""

    if "text/event-stream" in content_type or "application/json" not in content_type:
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8', errors='ignore')
                if line_str.startswith("data: ") and "[DONE]" not in line_str:
                    try:
                        data_json = json.loads(line_str[6:])
                        delta = data_json.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            full_text += delta["content"]
                    except:
                        pass
    else:
        try:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                full_text = data["choices"][0].get("message", {}).get("content", "")
        except:
            pass

    if full_text:
        history.append({"role": "assistant", "content": full_text})
        return full_text
    return None

def chat_chatai(user_input, history, model_id, active_proxy=None):
    history.append({"role": "user", "content": user_input})
    clean_history = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    payload = {"model": model_id, "messages": clean_history}

    if active_proxy:
        proxy_dict = {"http": active_proxy, "https": active_proxy}
        try:
            response = requests.post(
                CHATAI_URL,
                headers=CHATAI_HEADERS,
                json=payload,
                proxies=proxy_dict,
                stream=True,
                timeout=(6, 180)
            )
            if response.status_code == 200:
                result = parse_chatai_response(response, history)
                if result:
                    if "limitinize ulaştınız" in result.lower() or "günlük limit" in result.lower():
                        proxies = load_local_proxies()
                        if active_proxy in proxies:
                            proxies.remove(active_proxy)
                            proxies.append(active_proxy)
                            save_local_proxies(proxies)
                        active_proxy = None
                        history.pop()
                    else:
                        return result, active_proxy

            proxies = load_local_proxies()
            if response.status_code in [429, 403]:
                if active_proxy in proxies:
                    proxies.remove(active_proxy)
                    proxies.append(active_proxy)
                    save_local_proxies(proxies)
            else:
                if active_proxy in proxies:
                    proxies.remove(active_proxy)
                    save_local_proxies(proxies)
            active_proxy = None

        except Exception as e:
            logging.error(f"ChatAI proxy hatası: {e}")
            proxies = load_local_proxies()
            if active_proxy in proxies:
                proxies.remove(active_proxy)
                save_local_proxies(proxies)
            active_proxy = None

    if not active_proxy:
        proxies = load_local_proxies()
        try:
            response = requests.post(CHATAI_URL, headers=CHATAI_HEADERS, json=payload, stream=True, timeout=(4, 120))
            if response.status_code == 200:
                result = parse_chatai_response(response, history)
                if result and "limitinize ulaştınız" not in result.lower():
                    return result, None
        except Exception as e:
            logging.error(f"ChatAI doğrudan hata: {e}")

        if not proxies:
            history.pop()
            return None, None

        test_sample = proxies[:25]
        for proxy in test_sample:
            proxy_dict = {"http": proxy, "https": proxy}
            try:
                response = requests.post(
                    CHATAI_URL,
                    headers=CHATAI_HEADERS,
                    json=payload,
                    proxies=proxy_dict,
                    stream=True,
                    timeout=(4, 180)
                )
                if response.status_code == 200:
                    result = parse_chatai_response(response, history)
                    if result:
                        if "limitinize ulaştınız" in result.lower() or "günlük limit" in result.lower():
                            if proxy in proxies:
                                proxies.remove(proxy)
                                proxies.append(proxy)
                                save_local_proxies(proxies)
                        else:
                            return result, proxy

                if response.status_code in [429, 403]:
                    if proxy in proxies:
                        proxies.remove(proxy)
                        proxies.append(proxy)
                        save_local_proxies(proxies)
                else:
                    if proxy in proxies:
                        proxies.remove(proxy)
                        save_local_proxies(proxies)

            except Exception as e:
                logging.error(f"ChatAI proxy test hatası: {e}")
                if proxy in proxies:
                    proxies.remove(proxy)
                    save_local_proxies(proxies)

        history.pop()
        return None, None