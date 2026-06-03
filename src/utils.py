import requests
from io import BytesIO
from PIL import Image

try:
    import win32clipboard
    _WIN32 = True
except ImportError:
    _WIN32 = False

# Headers de browser real para evitar 403 em servidores que bloqueiam bots
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
}


def _exige_windows(fn_name: str):
    if not _WIN32:
        raise RuntimeError(f"{fn_name} requer Windows (win32clipboard indisponível).")


def _baixar_imagem(url: str) -> Image.Image:
    """Baixa imagem com headers de browser para evitar bloqueio 403."""
    resp = requests.get(url, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content)).convert("RGB")


def copiar_texto_para_clipboard(texto: str):
    _exige_windows("copiar_texto_para_clipboard")
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, texto)
    finally:
        win32clipboard.CloseClipboard()


def copiar_imagem_para_clipboard(url: str):
    _exige_windows("copiar_imagem_para_clipboard")
    img = _baixar_imagem(url)
    buf = BytesIO()
    img.save(buf, "BMP")
    dados = buf.getvalue()[14:]
    buf.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dados)
    finally:
        win32clipboard.CloseClipboard()


def redimensionar_imagem(url: str):
    """Baixa a imagem e retorna BytesIO JPEG. Retorna None se falhar."""
    try:
        img = _baixar_imagem(url)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"[utils] Erro ao baixar/redimensionar imagem: {e!r}")
        return None
