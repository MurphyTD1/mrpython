import os
import re
import subprocess
import requests
import urllib.parse
from config import BASE_DIR, logging

# Real-ESRGAN
REALESRGAN_DIR = os.path.join(BASE_DIR, "Real-ESRGAN")
REALESRGAN_EXE = os.path.join(REALESRGAN_DIR, "realesrgan-ncnn-vulkan.exe")
REALESRGAN_AVAILABLE = os.path.exists(REALESRGAN_EXE)

# Resimlerin kaydedileceği klasör
RESIM_KLASORU = os.path.join(BASE_DIR, "resimler")
os.makedirs(RESIM_KLASORU, exist_ok=True)

# Pollinations
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"

# DeepAI Image
DEEPAI_IMAGE_API_KEY = "tryit-16772144325-9775e41ecb184dba238e463de8b83da9"
DEEPAI_IMAGE_HEADERS = {
    "Api-Key": DEEPAI_IMAGE_API_KEY,
    "Cookie": "user_sees_ads=true",
    "Origin": "https://deepai.org",
    "Referer": "https://deepai.org/machine-learning-model/text2img",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_quality_options():
    options = {
        "1": {"label": "Düşük (512x512)", "width": 512, "height": 512},
        "2": {"label": "Orta (768x768)", "width": 768, "height": 768},
        "3": {"label": "Yüksek (1024x1024)", "width": 1024, "height": 1024}
    }
    if REALESRGAN_AVAILABLE:
        options["4"] = {"label": "4K AI (Ultra)", "width": None, "height": None}
        options["5"] = {"label": "4K AI (TTA - Yüksek Kalite, Yavaş)", "width": None, "height": None}
    return options

def enhance_prompt_deepai(prompt):
    url = "https://api.deepai.org/enhance_prompt"
    files = {
        'prompt': (None, prompt),
        'context_type': (None, 'image_generation')
    }
    try:
        response = requests.post(url, headers=DEEPAI_IMAGE_HEADERS, files=files, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("output", prompt)
        else:
            return prompt
    except Exception as e:
        logging.error(f"Prompt geliştirme hatası: {e}")
        return prompt

def translate_text(text, target_lang="en"):
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&ie=UTF-8&oe=UTF-8&q={encoded}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            translated = data[0][0][0]
            return translated if translated else text
        return text
    except Exception as e:
        logging.error(f"Çeviri hatası: {e}")
        return text

def generate_image_pollinations(prompt, width=1024, height=1024, original_prompt=None):
    name_source = original_prompt if original_prompt else prompt
    words = re.findall(r'\w+', name_source)
    base_name = '_'.join(words[:4]) if words else "resim"
    base_name = re.sub(r'[^a-zA-Z0-9_]', '', base_name)
    if not base_name:
        base_name = "resim"
    if len(base_name) > 50:
        base_name = base_name[:50]

    counter = 0
    while True:
        filename = f"{base_name}.jpg" if counter == 0 else f"{base_name}_{counter}.jpg"
        filepath = os.path.join(RESIM_KLASORU, filename)
        if not os.path.exists(filepath):
            break
        counter += 1

    encoded_prompt = requests.utils.quote(prompt)
    url = f"{POLLINATIONS_URL}{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true"

    try:
        response = requests.get(url, timeout=90)
        if response.status_code != 200:
            return None
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        logging.error(f"Resim oluşturma hatası: {e}")
        return None

def run_realesrgan(input_path, output_suffix, tta=False):
    if not os.path.exists(REALESRGAN_EXE):
        return None

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}{output_suffix}.png"

    cmd = [
        REALESRGAN_EXE,
        "-i", input_path,
        "-o", output_path,
        "-n", "realesrgan-x4plus"
    ]
    if tta:
        cmd.append("-x")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            pass  # İlerlemeyi yoksay (bot için)
        process.wait()
        if process.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            return None
    except Exception as e:
        logging.error(f"Real-ESRGAN hatası: {e}")
        return None