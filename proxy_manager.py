import os
from config import BASE_DIR

PROXY_FILE = os.path.join(BASE_DIR, "all-proxies.txt")

def get_proxy_filepath():
    target = PROXY_FILE
    if not os.path.exists(target):
        alt = os.path.join(BASE_DIR, "all-proxies.txt.txt")
        if os.path.exists(alt):
            return alt
    return target

def load_local_proxies():
    path = get_proxy_filepath()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                formatted = []
                for p in lines:
                    if not (p.startswith("http://") or p.startswith("https://") or
                            p.startswith("socks4://") or p.startswith("socks5://")):
                        formatted.append(f"http://{p}")
                    else:
                        formatted.append(p)
                return formatted
        except Exception:
            pass
    return []

def save_local_proxies(proxies):
    path = get_proxy_filepath()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(proxies) + ("\n" if proxies else ""))
    except Exception:
        pass