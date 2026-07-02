import asyncio
import concurrent.futures
from flask import Flask, render_template, request, jsonify

from src.ai.message_processor import montar_mensagem
from src.services.whatsapp_bot import enviar_whatsapp_grupo, enviar_whatsapp_canal
from src.services.telegram_bot import enviar_telegram
from src.utils import processar_imagem_altura_fixa_base64

app = Flask(__name__)
app.secret_key = "troque-por-chave-segura-em-producao"

_CAMPOS_OBRIGATORIOS = ["nome", "preco", "descricao", "link", "imagem"]


def _run_async(coro):
    """Executa coroutine de forma segura independente do estado do event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _coletar_dados_formulario(form):
    """Coleta e valida os campos obrigatórios do formulário. Retorna (dados, erro)."""
    dados = {c: form.get(c, "").strip() for c in _CAMPOS_OBRIGATORIOS}
    faltando = [c for c, v in dados.items() if not v]
    if faltando:
        return None, f"Campos obrigatórios: {', '.join(faltando)}"

    dados["cupom"] = form.get("cupom", "").strip() or None
    dados["observacao"] = form.get("observacao", "").strip() or None
    return dados, None


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/enviar", methods=["POST"])
def enviar():
    """
    Endpoint único (AJAX) que processa todo o envio da oferta.

    - Gera as mensagens via IA (WhatsApp e Telegram).
    - WhatsApp (Grupo/Canal):
        * modo "automatico" -> dispara Selenium normalmente.
        * modo "manual"     -> NÃO dispara nada; o front-end usa
          'mensagem_whatsapp' e 'imagem_url' do retorno para montar
          o bloco de cópia (imagem + texto).
    - Telegram: sempre automático, sem alterações no fluxo.

    Retorna JSON com o resultado de cada destino, mais a mensagem/imagem
    do WhatsApp para o bloco manual (gerados sempre, independente das
    checkboxes, para que o usuário possa copiar mesmo sem marcar
    Grupo/Canal).
    """
    dados, erro = _coletar_dados_formulario(request.form)
    if erro:
        return jsonify({"erro": erro}), 400

    enviar_grupo  = bool(request.form.get("destino_grupo"))
    enviar_canal  = bool(request.form.get("destino_canal"))
    enviar_tg     = bool(request.form.get("destino_telegram"))
    modo_whatsapp = request.form.get("modo_whatsapp", "automatico")

    if not any([enviar_grupo, enviar_canal, enviar_tg]):
        return jsonify({"erro": "Selecione pelo menos um destino para enviar."}), 400

    # Monta mensagens via IA
    try:
        mensagem_whatsapp = montar_mensagem(
            dados["nome"], dados["preco"], dados["descricao"],
            dados["link"], dados["cupom"], dados["observacao"],
            plataforma="whatsapp"
        )
        mensagem_telegram = montar_mensagem(
            dados["nome"], dados["preco"], dados["descricao"],
            dados["link"], dados["cupom"], dados["observacao"],
            plataforma="telegram"
        )
    except Exception as e:
        return jsonify({"erro": f"Erro ao gerar mensagem: {e}"}), 500

    resultados = []
    erros      = []
    modo_manual_ativo = False

    # ── WhatsApp (Grupo/Canal) ──
    if modo_whatsapp == "manual":
        # Não dispara Selenium. O front-end exibe o bloco de cópia manual
        # usando mensagem_whatsapp / imagem_url retornados abaixo.
        modo_manual_ativo = True
    else:
        if enviar_grupo:
            ok = enviar_whatsapp_grupo(mensagem_whatsapp, dados["imagem"])
            (resultados if ok else erros).append("Grupo")

        if enviar_canal:
            ok = enviar_whatsapp_canal(mensagem_whatsapp, dados["imagem"])
            (resultados if ok else erros).append("Canal")

    # ── Telegram — sempre automático, sem alterações ──
    if enviar_tg:
        try:
            _run_async(enviar_telegram(mensagem_telegram, dados["imagem"]))
            resultados.append("Telegram")
        except Exception as e:
            print(f"[app] Erro Telegram: {e!r}")
            erros.append("Telegram")

    # Gera a imagem redimensionada PROPORCIONALMENTE para 300px de altura
    # (sem cortar nada) para uso no bloco manual — evita problemas de CORS
    # que o navegador teria ao buscar a imagem original diretamente via fetch().
    imagem_300 = processar_imagem_altura_fixa_base64(dados["imagem"], altura_destino=300)

    return jsonify({
        "resultados": resultados,
        "erros": erros,
        "modo_manual_ativo": modo_manual_ativo,
        "mensagem_whatsapp": mensagem_whatsapp,
        "imagem_url": dados["imagem"],
        "imagem_300": imagem_300,
    })


@app.route("/preview", methods=["POST"])
def preview():
    """Endpoint AJAX: retorna prévia da mensagem sem enviar."""
    dados = request.get_json(silent=True) or {}
    nome  = dados.get("nome", "").strip()
    preco = dados.get("preco", "").strip()
    desc  = dados.get("descricao", "").strip()
    link  = dados.get("link", "").strip()
    cupom = dados.get("cupom", "").strip() or None
    obs   = dados.get("observacao", "").strip() or None

    if not all([nome, preco, desc, link]):
        return jsonify({"erro": "Preencha nome, preço, descrição e link para pré-visualizar."}), 400

    try:
        mensagem_whatsapp = montar_mensagem(nome, preco, desc, link, cupom, obs, plataforma="whatsapp")
        mensagem_telegram = montar_mensagem(nome, preco, desc, link, cupom, obs, plataforma="telegram")
        return jsonify({"whatsapp": mensagem_whatsapp, "telegram": mensagem_telegram})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
