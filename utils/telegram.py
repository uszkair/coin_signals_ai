from telegram import Bot
from telegram.constants import ParseMode
import asyncio

# IDE ÍRD BE A SAJÁT TOKENED ÉS CHAT ID-T
TELEGRAM_TOKEN = "7517040562:AAH3tIjke9gXfBuc_EvQpdhpUS0Gm3kB_pc"
CHAT_ID = 5742159599

bot = Bot(token=TELEGRAM_TOKEN)

def send_signal_message(symbol, price, signal, rsi, ema):
    message = (
        f"Jelzés érkezett:\n"
        f"Szimbólum: {symbol}\n"
        f"Ár: {price:.2f} USD\n"
        f"RSI: {rsi:.2f}\n"
        f"EMA20: {ema:.2f}\n"
        f"Javaslat: {signal}"
    )
    bot.send_message(chat_id=CHAT_ID, text=message)