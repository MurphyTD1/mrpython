from flask import Flask, send_from_directory
import threading
import os
from config import BASE_DIR

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

def start_bot():
    import bot
    bot.bot.infinity_polling()

if __name__ == '__main__':
    # Bot'u ayrı thread'de çalıştır
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    # Flask'ı başlat
    app.run(host='0.0.0.0', port=5000, debug=False)