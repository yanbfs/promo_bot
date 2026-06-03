import time
import requests
from src.config.config import OPENAI_API_KEY

_URL = "https://api.openai.com/v1/chat/completions"
_HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}


def chamar_openai(messages: list, temperature: float = 0.7, max_tokens: int = 300, max_retries: int = 5) -> str:
    """
    Chama gpt-4o-mini com retry exponencial limitado.
    Lança RuntimeError se esgotar todas as tentativas.
    """
    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    backoff = 1
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(_URL, headers=_HEADERS, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.HTTPError as e:
            status = e.response.status_code
            if status == 429:
                ra = e.response.headers.get("Retry-After")
                wait = int(ra) if ra and ra.isdigit() else backoff
                print(f"[OpenAI] 429 – aguardando {wait}s (tentativa {attempt}/{max_retries})")
            else:
                wait = backoff
                print(f"[OpenAI] HTTP {status} – retentando em {wait}s (tentativa {attempt}/{max_retries})")
        except Exception as e:
            wait = backoff
            print(f"[OpenAI] Erro: {e!r} – retentando em {wait}s (tentativa {attempt}/{max_retries})")

        time.sleep(wait)
        backoff = min(backoff * 2, 60)

    raise RuntimeError(f"[OpenAI] API indisponível após {max_retries} tentativas.")
