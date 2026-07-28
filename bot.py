import os
import requests

# GitHub Secrets'tan gelen değişkenler
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

def get_cyber_fact():
    try:
        # Çalışan rastgele bilgi API'si
        url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("text", "Bilgi çekilemedi.")
        return "Bilgi servisine ulaşılamadı."
    except Exception as e:
        print(f"API Hatası: {e}")
        return "Sistem hatası oluştu."

def send_telegram(text):
    if not TELEGRAM_TOKEN or not CHANNEL_ID:
        print("❌ Hata: TELEGRAM_TOKEN veya CHANNEL_ID Secret'ları bulunamadı!")
        return
        
    # Telegram API endpoint'i düzeltildi
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": f"🤖 **[Günün Bilgisi]**\n\n{text}",
        "parse_mode": "Markdown"
    }
    
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        print("✅ Mesaj Telegram'a başarıyla gönderildi!")
    else:
        print(f"❌ Telegram Hatası ({res.status_code}): {res.text}")

if __name__ == "__main__":
    fact = get_cyber_fact()
    send_telegram(fact)
