from telegram import Bot
from src.config.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from src.utils import redimensionar_imagem

async def enviar_telegram(mensagem_completa, img_url):
    bot = Bot(token=TELEGRAM_TOKEN)
    buf = redimensionar_imagem(img_url)
    if buf:
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=buf,
                             caption=mensagem_completa, parse_mode="HTML")
    else:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                               text=mensagem_completa, parse_mode="HTML")
