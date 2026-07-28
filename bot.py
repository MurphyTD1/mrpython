import telebot
import threading
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import get_telegram_token, get_admin_chat_id, is_banned, is_vip, add_ban, remove_ban, add_vip, remove_vip, logging
from chat_apis import MODELS, chat_freellm, chat_deepai, chat_chatai
from resim_olusturucu import (
    generate_image_pollinations, enhance_prompt_deepai, translate_text,
    get_quality_options, run_realesrgan, RESIM_KLASORU, REALESRGAN_AVAILABLE
)
from wormgpt import WORMGPT_SYSTEM_PROMPT

TOKEN = get_telegram_token()
if not TOKEN:
    raise ValueError("Telegram token bulunamadı! config.json dosyasını düzenleyin.")

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# Kullanıcı oturumları
user_sessions = {}       # user_id -> {'model': '1', 'history': [], 'active_proxy': None}
user_temp = {}           # user_id -> {'prompt': '', 'enhance': False, 'quality': None}

def get_user_model(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {'history': [], 'active_proxy': None, 'model': '1'}  # varsayılan ChatGPT
    return user_sessions[user_id].get('model', '1')

def set_user_model(user_id, model_key):
    if user_id not in user_sessions:
        user_sessions[user_id] = {'history': [], 'active_proxy': None}
    user_sessions[user_id]['model'] = model_key

def get_user_history(user_id):
    return user_sessions.get(user_id, {}).get('history', [])

def clear_user_history(user_id):
    if user_id in user_sessions:
        user_sessions[user_id]['history'] = []

def get_user_proxy(user_id):
    return user_sessions.get(user_id, {}).get('active_proxy')

def set_user_proxy(user_id, proxy):
    if user_id not in user_sessions:
        user_sessions[user_id] = {'history': [], 'active_proxy': None}
    user_sessions[user_id]['active_proxy'] = proxy

def send_message_safe(chat_id, text, parse_mode='MarkdownV2', **kwargs):
    try:
        return bot.send_message(chat_id, text, parse_mode=parse_mode, **kwargs)
    except Exception as e:
        logging.error(f"Markdown hatası, düz metin gönderiliyor: {e}")
        return bot.send_message(chat_id, text, parse_mode=None, **kwargs)

def reply_to_safe(message, text, parse_mode='MarkdownV2', **kwargs):
    try:
        return bot.reply_to(message, text, parse_mode=parse_mode, **kwargs)
    except Exception as e:
        logging.error(f"Markdown hatası, düz metin gönderiliyor: {e}")
        return bot.reply_to(message, text, parse_mode=None, **kwargs)

# ---------- KOMUTLAR ----------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Bu botu kullanma izniniz yok.")
        return
    welcome_text = (
        "🤖 **Hoş Geldiniz!**\n\n"
        "Bu bot, çeşitli AI modellerini kullanarak sohbet edebilir, resim oluşturabilir.\n\n"
        "📌 **Komutlar:**\n"
        "/model - Model seçimi yapın\n"
        "/resim - Resim oluşturun\n"
        "/clear - Sohbet geçmişini temizleyin\n"
        "/start - Bu mesajı gösterir\n\n"
        "İlk önce /model ile bir model seçin, ardından sohbet edebilirsiniz. Varsayılan model ChatGPT'dir."
    )
    send_message_safe(message.chat.id, welcome_text)

@bot.message_handler(commands=['model'])
def model_list(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "Banlısınız.")
        return
    markup = InlineKeyboardMarkup()
    for key, model in MODELS.items():
        markup.add(InlineKeyboardButton(f"{model['name']}", callback_data=f"model_{key}"))
    send_message_safe(message.chat.id, "🤖 **Model Seçin:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def model_selection(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "Banlısınız!", show_alert=True)
        return
    model_key = call.data.split('_')[1]
    set_user_model(user_id, model_key)
    model_name = MODELS[model_key]['name']
    bot.answer_callback_query(call.id, f"✅ Model {model_name} seçildi.")
    bot.edit_message_text(f"✅ Model {model_name} seçildi. Şimdi sohbet edebilirsiniz.", call.message.chat.id, call.message.message_id)
    send_message_safe(call.message.chat.id, "💬 Mesajınızı yazın. /clear ile geçmişi temizleyin.")

@bot.message_handler(commands=['clear'])
def clear(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "Banlısınız.")
        return
    clear_user_history(user_id)
    bot.reply_to(message, "🧹 Sohbet geçmişi temizlendi.")

@bot.message_handler(commands=['resim'])
def resim_command(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Banlısınız.")
        return
    msg = bot.reply_to(message, "📝 Resim açıklamasını yazın:")
    bot.register_next_step_handler(msg, process_resim_prompt)

def process_resim_prompt(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "Banlısınız.")
        return
    prompt = message.text.strip()
    if not prompt:
        bot.reply_to(message, "❌ Açıklama boş olamaz. Tekrar /resim yapın.")
        return
    user_temp[user_id] = {'prompt': prompt, 'enhance': False, 'quality': None}
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✨ Evet", callback_data="img_enhance_yes"),
               InlineKeyboardButton("Hayır", callback_data="img_enhance_no"))
    send_message_safe(message.chat.id, "Prompt geliştirilsin mi?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('img_enhance_'))
def img_enhance_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "Banlısınız!", show_alert=True)
        return
    if user_id not in user_temp:
        bot.answer_callback_query(call.id, "Önce /resim komutunu kullanın.", show_alert=True)
        return
    if call.data == 'img_enhance_yes':
        user_temp[user_id]['enhance'] = True
    else:
        user_temp[user_id]['enhance'] = False
    bot.answer_callback_query(call.id, "Tamam.")
    quality_options = get_quality_options()
    markup = InlineKeyboardMarkup()
    for key, opt in quality_options.items():
        markup.add(InlineKeyboardButton(f"{opt['label']}", callback_data=f"img_quality_{key}"))
    send_message_safe(call.message.chat.id, "Kalite seçin:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('img_quality_'))
def img_quality_callback(call):
    user_id = call.from_user.id
    if is_banned(user_id):
        bot.answer_callback_query(call.id, "Banlısınız!", show_alert=True)
        return
    quality_key = call.data.split('_')[2]
    if user_id not in user_temp:
        bot.answer_callback_query(call.id, "Hata, lütfen /resim ile baştan başlayın.", show_alert=True)
        return
    user_temp[user_id]['quality'] = quality_key
    bot.answer_callback_query(call.id, "Resim oluşturuluyor...")
    threading.Thread(target=generate_and_send_image, args=(call.message.chat.id, user_id)).start()

def generate_and_send_image(chat_id, user_id):
    try:
        data = user_temp.get(user_id)
        if not data:
            send_message_safe(chat_id, "❌ Bir hata oluştu, lütfen /resim ile tekrar deneyin.")
            return
        prompt = data['prompt']
        enhance = data['enhance']
        quality_key = data['quality']
        prompt_en = translate_text(prompt)
        if enhance:
            prompt_en = enhance_prompt_deepai(prompt_en)
        quality_options = get_quality_options()
        opt = quality_options.get(quality_key)
        if not opt:
            opt = quality_options['2']
        width = opt['width']
        height = opt['height']

        if quality_key in ['4', '5']:
            temp_file = generate_image_pollinations(prompt_en, 1024, 1024, original_prompt=prompt)
            if not temp_file:
                send_message_safe(chat_id, "❌ Resim oluşturulamadı.")
                return
            tta = (quality_key == '5')
            output_path = run_realesrgan(temp_file, "_4k" if not tta else "_4k_tta", tta=tta)
            if output_path:
                with open(output_path, 'rb') as f:
                    bot.send_photo(chat_id, f, caption="✅ 4K yükseltme tamamlandı.")
                try: os.remove(temp_file)
                except: pass
            else:
                with open(temp_file, 'rb') as f:
                    bot.send_photo(chat_id, f, caption="⚠️ Yükseltme başarısız, orijinal resim.")
        else:
            filepath = generate_image_pollinations(prompt_en, width, height, original_prompt=prompt)
            if filepath:
                with open(filepath, 'rb') as f:
                    bot.send_photo(chat_id, f, caption="✅ Resim oluşturuldu.")
            else:
                send_message_safe(chat_id, "❌ Resim oluşturulamadı.")
    except Exception as e:
        logging.error(f"Resim oluşturma hatası: {e}")
        send_message_safe(chat_id, "❌ Bir hata oluştu.")
    finally:
        if user_id in user_temp:
            del user_temp[user_id]

# ---------- YÖNETİCİ KOMUTLARI ----------
@bot.message_handler(commands=['ban'])
def ban_user(message):
    user_id = message.from_user.id
    if user_id != get_admin_chat_id():
        bot.reply_to(message, "Bu komut sadece admin içindir.")
        return
    try:
        target_id = int(message.text.split()[1])
    except:
        bot.reply_to(message, "Kullanım: /ban <user_id>")
        return
    add_ban(target_id)
    bot.reply_to(message, f"Kullanıcı {target_id} banlandı.")

@bot.message_handler(commands=['unban'])
def unban_user(message):
    user_id = message.from_user.id
    if user_id != get_admin_chat_id():
        bot.reply_to(message, "Bu komut sadece admin içindir.")
        return
    try:
        target_id = int(message.text.split()[1])
    except:
        bot.reply_to(message, "Kullanım: /unban <user_id>")
        return
    remove_ban(target_id)
    bot.reply_to(message, f"Kullanıcı {target_id} banı kaldırıldı.")

@bot.message_handler(commands=['vip'])
def add_vip_user(message):
    user_id = message.from_user.id
    if user_id != get_admin_chat_id():
        bot.reply_to(message, "Bu komut sadece admin içindir.")
        return
    try:
        target_id = int(message.text.split()[1])
    except:
        bot.reply_to(message, "Kullanım: /vip <user_id>")
        return
    add_vip(target_id)
    bot.reply_to(message, f"Kullanıcı {target_id} VIP eklendi.")

# ---------- SOYBEK MESAJLARI ----------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Banlısınız.")
        return
    # Eğer mesaj komut ile başlıyorsa işleme alma (güvenlik)
    if message.text and message.text.startswith('/'):
        return

    model_key = get_user_model(user_id)
    model = MODELS.get(model_key)
    if not model:
        model = MODELS['1']
    source = model['source']
    model_id = model['model_id']
    history = get_user_history(user_id)
    user_input = message.text

    # İşlem yapıldığını belirten yazı
    bot.send_chat_action(message.chat.id, 'typing')

    if source == 'wormgpt':
        wrapped = f"{WORMGPT_SYSTEM_PROMPT}\n\nKullanıcı sorusu: {user_input}"
        cevap = chat_deepai(wrapped, history, model_id, system_prompt=None)
    elif source == 'deepai':
        cevap = chat_deepai(user_input, history, model_id)
    elif source == 'chatai':
        if model_id is None:  # FreeLLM
            cevap = chat_freellm(user_input, history)
        else:
            active_proxy = get_user_proxy(user_id)
            cevap, new_proxy = chat_chatai(user_input, history, model_id, active_proxy)
            if new_proxy:
                set_user_proxy(user_id, new_proxy)
    else:
        cevap = None

    if cevap:
        reply_to_safe(message, cevap)
    else:
        bot.reply_to(message, "⚠️ Yanıt alınamadı, lütfen tekrar deneyin.")