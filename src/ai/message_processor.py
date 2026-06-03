import re
import random
import html
from src.ai.ai_service import chamar_openai
from src.config.config import (
    LINK_WHATSAPP,
    LINK_WHATSAPP_CANAL,
    LINK_TELEGRAM,
)

_SEPARADORES = (":", "–", "—", " - ")

_FRASES_CTA = [
    "🛒 Pega o link e garanta já:",
    "💰 Quer levar? Só clicar aqui:",
    "🔗 Acesse o link da oferta:",
    "👉 Confira no link:",
    "🛍️ Compra direta neste link:",
    "💵 Link com o valor atualizado:",
    "📦 Produto disponível no link:",
    "🚀 Acesse a oferta agora:",
    "📲 Link para compra:",
    "🔗 Link oficial do produto:",
    "📌 Oferta disponível aqui:",
    "🛒 Acesse para comprar:",
]


# ── Formatação de preço ──────────────────────────────────────────────────────

def formatar_preco(preco_str: str) -> str:
    if not preco_str:
        return "R$ 0,00"
    s = re.sub(r'(?i)r\$\s*', '', preco_str).strip().replace(' ', '')
    s = re.sub(r'[^0-9\.,]', '', s)
    if not s:
        return "R$ 0,00"

    if '.' in s and ',' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace('.', '').replace(',', '.') if re.search(r',\d{1,2}$', s) else s.replace(',', '')
    elif '.' in s:
        if not re.search(r'\.\d{1,2}$', s):
            s = s.replace('.', '')

    try:
        valor = float(s)
    except ValueError:
        digits = re.sub(r'\D', '', preco_str)
        if not digits:
            return "R$ 0,00"
        valor = int(digits[:-2]) + int(digits[-2:]) / 100.0 if len(digits) > 2 else int(digits) / 100.0

    fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return fmt


# ── Geração de conteúdo via IA ───────────────────────────────────────────────

def _gerar_nome_e_descricao(nome: str, descricao: str, tentativa: int = 0) -> tuple[str, str]:
    if tentativa >= 3:
        print("[IA] Limite de tentativas atingido — usando texto original.")
        return nome, descricao[:120]

    prompt = f"""
Responda obrigatoriamente em português.

Você é um redator TÉCNICO de produtos para posts de promoções.

OBJETIVO:
Gerar uma descrição curta, objetiva e técnica, destacando APENAS características reais do produto.

REGRAS OBRIGATÓRIAS:
- NÃO use verbos promocionais ou emocionais, como:
  "transforme", "desfrute", "ideal para", "perfeito para", 
  "experimente", "sinta", "eleva", "aproveite", "incrível", "potente".
- NÃO use frases genéricas de marketing.
- NÃO faça chamada de venda.
- NÃO invente benefícios subjetivos.
- NÃO use linguagem emocional.

FAÇA:
- Destaque especificações técnicas, medidas, números, materiais, tecnologias ou diferenciais concretos.
- Use frases curtas e informativas.
- Use no máximo 2 linhas para a descrição.
- Linguagem direta, objetiva e factual.

FORMATO DE RESPOSTA (OBRIGATÓRIO):
Linha 1: Nome do produto (mantenha o nome original, adicione 1 emoji no início e 1 no fim).
Linha 2: Descrição técnica objetiva (1 emoji no início e 1 no fim).

Produto:
{nome}

Descrição original (use apenas como referência técnica, sem copiar frases):
{descricao}
"""

    try:
        resposta = chamar_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        linhas = [l.strip() for l in resposta.splitlines() if l.strip()]
        if len(linhas) >= 2:
            nome_ia = linhas[0]
            for sep in _SEPARADORES:
                if sep in nome_ia:
                    nome_ia = nome_ia.split(sep)[0].strip()
                    break
            return nome_ia, linhas[1]
        print(f"[IA] Resposta inválida (< 2 linhas), tentativa {tentativa + 1}/3")
        return _gerar_nome_e_descricao(nome, descricao, tentativa + 1)
    except RuntimeError as e:
        print(f"[IA] {e}")
        return nome, descricao[:120]


def _reescrever_observacao(obs: str) -> str:
    prompt = f"""Revise e corrija ortografia, resuma em 1 linha casual e direta, sem clichês.
Texto: {obs}
Responda apenas a versão reescrita."""
    try:
        return chamar_openai(
            [{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=60,
        ).splitlines()[0].strip()
    except RuntimeError:
        return obs


# ── Montagem do rodapé de links ──────────────────────────────────────────────

def _montar_rodape() -> str:
    """
    Monta o bloco '⚡️ Entre nos grupos!' dinamicamente.
    Só inclui cada linha se o link correspondente estiver preenchido no .env.
    """
    linhas = ["⚡️ Entre nos grupos!"]

    if LINK_WHATSAPP:
        linhas.append(f"👉 Grupo do WhatsApp: {LINK_WHATSAPP}")
    if LINK_WHATSAPP_CANAL:
        linhas.append(f"👉 Canal do WhatsApp: {LINK_WHATSAPP_CANAL}")
    if LINK_TELEGRAM:
        linhas.append(f"👉 Telegram: {LINK_TELEGRAM}")

    # Se não tiver nenhum link, não exibe o bloco
    if len(linhas) == 1:
        return ""

    return "\n".join(linhas)


# ── Montagem da mensagem final ───────────────────────────────────────────────

def montar_mensagem(nome: str, preco: str, descricao: str, link: str,
                    cupom: str | None = None, obs: str | None = None,
                    plataforma: str = "whatsapp") -> str:

    nome_ia, desc_ia = _gerar_nome_e_descricao(nome, descricao)
    preco_fmt = formatar_preco(preco)
    obs_fmt = _reescrever_observacao(obs) if obs else None

    # Formatação do cupom por plataforma
    if cupom:
        if plataforma == "telegram":
            cupom_formatado = f"<code>{html.escape(cupom)}</code>"
        else:
            cupom_formatado = f"*`{cupom}`*"
        cupom_linha = f"\n🏷️ Cupom: {cupom_formatado}"
    else:
        cupom_linha = ""

    obs_linha = f"\n📝 {obs_fmt}" if obs_fmt else ""
    frase_cta = random.choice(_FRASES_CTA)
    rodape    = _montar_rodape()
    rodape_bloco = f"\n\n{rodape}" if rodape else ""

    return (
        f"🔥 {nome_ia} 🔥\n\n"
        f"🛍️ {desc_ia}\n\n"
        f"💰 Por apenas: {preco_fmt}"
        f"{cupom_linha}"
        f"{obs_linha}"
        f"\n\n{frase_cta}\n{link}"
        f"{rodape_bloco}"
    )
