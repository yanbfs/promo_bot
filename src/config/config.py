import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID", "")
WHATSAPP_GRUPO    = os.getenv("WHATSAPP_GRUPO", "")
WHATSAPP_CANAL    = os.getenv("WHATSAPP_CANAL", "")
WHATSAPP_PERFIL   = os.getenv("WHATSAPP_PERFIL", "./perfil_chrome")
LINK_WHATSAPP       = os.getenv("LINK_WHATSAPP", "")
LINK_WHATSAPP_CANAL = os.getenv("LINK_WHATSAPP_CANAL", "")
LINK_TELEGRAM       = os.getenv("LINK_TELEGRAM", "")
