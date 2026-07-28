import requests 
import os
# Telegram Bot Bilgileri# Güvenlik için tokenları doğrudan koda yazmıyoruz, GitHub Secrets'tan çekeceğiz!TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")CHANNEL_ID = os.getenv("CHANNEL_ID")
def get_cyber_fact():
    try:
        # Örnek olarak ücretsiz bir API'den gereksiz/ilginç bilgi çekiyoruz
        url = "https://jsph.pl"
        response = requests.get(url)
        return response.json().get("text", "Bilgi çekilemedi.")
    except:
        return "Sistem hatası."
def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        print("Hata: Telegram API anahtarları eksik!")
        return
        
    url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": f"🤖 **[Sunucusuz Bot Sistemi]**\n\n{text}",
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)
    print("Mesaj Telegram'a gönderildi!")
if __name__ == "__main__":
    fact = get_cyber_fact()
    send_telegram(fact)
