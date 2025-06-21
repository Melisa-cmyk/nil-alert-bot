from flask import Flask
import threading
import time
import requests
from telegram import Bot

app = Flask(__name__)

# 🔐 Kendi bilgilerini buraya gir
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
bot = Bot(token=TELEGRAM_BOT_TOKEN)
BINANCE_API_URL = "https://fapi.binance.com"

def get_rsi(symbol="NILUSDT", interval="5m", limit=100):
    url = f"{BINANCE_API_URL}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    closes = [float(x[4]) for x in requests.get(url).json()]
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    return 100 - (100 / (1 + rs))

def get_funding(symbol="NILUSDT"):
    url = f"{BINANCE_API_URL}/fapi/v1/fundingRate?symbol={symbol}&limit=1"
    return float(requests.get(url).json()[0]["fundingRate"])

def get_long_short_ratio(symbol="NILUSDT"):
    url = f"{BINANCE_API_URL}/futures/data/globalLongShortAccountRatio?symbol={symbol}&period=5m&limit=1"
    return float(requests.get(url).json()[0]["longShortRatio"])

def monitor():
    while True:
        try:
            rsi = get_rsi()
            funding = get_funding()
            ratio = get_long_short_ratio()
            if rsi < 30 and funding < -0.001 and ratio < 0.95:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"📉 RSI: {rsi:.2f} Funding: {funding:.5f} L/S: {ratio:.2f}")
            elif rsi > 70 and funding > 0.001 and ratio > 1.2:
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"📈 RSI: {rsi:.2f} Funding: {funding:.5f} L/S: {ratio:.2f}")
        except Exception as e:
            print("Hata:", e)
        time.sleep(300)

threading.Thread(target=monitor).start()

@app.route('/')
def home():
    return "Bot çalışıyor!"

