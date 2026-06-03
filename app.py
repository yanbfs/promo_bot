import asyncio
import concurrent.futures
from flask import Flask, render_template, request, redirect, flash, jsonify

from src.ai.message_processor import montar_mensagem
from src.services.whatsapp_bot import enviar_whatsapp_grupo, enviar_whatsapp_canal
from src.services.telegram_bot import enviar_telegram

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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Coleta e valida campos obrigatórios
        dados = {c: request.form.get(c, "").strip() for c in _CAMPOS_OBRIGATORIOS}
        faltando = [c for c, v in dados.items() if not v]
        if faltando:
            flash(f"Campos obrigatórios: {', '.join(faltando)}", "error")
            return redirect("/")

        # Lê os destinos selecionados
        enviar_grupo    = bool(request.form.get("destino_grupo"))
        enviar_canal    = bool(request.form.get("destino_canal"))
        enviar_tg       = bool(request.form.get("destino_telegram"))

        if not any([enviar_grupo, enviar_canal, enviar_tg]):
            flash("Selecione pelo menos um destino para enviar.", "error")
            return redirect("/")

        cupom = request.form.get("cupom", "").strip() or None
        obs   = request.form.get("observacao", "").strip() or None

        # Monta mensagens via IA
        try:
            mensagem_whatsapp = montar_mensagem(
                dados["nome"], dados["preco"], dados["descricao"],
                dados["link"], cupom, obs,
                plataforma="whatsapp"
            )
            mensagem_telegram = montar_mensagem(
                dados["nome"], dados["preco"], dados["descricao"],
                dados["link"], cupom, obs,
                plataforma="telegram"
            )
        except Exception as e:
            flash(f"Erro ao gerar mensagem: {e}", "error")
            return redirect("/")

        resultados = []
        erros      = []

        # ── Grupo ──
        if enviar_grupo:
            ok = enviar_whatsapp_grupo(mensagem_whatsapp, dados["imagem"])
            if ok:
                resultados.append("Grupo")
            else:
                erros.append("Grupo")

        # ── Canal ──
        if enviar_canal:
            ok = enviar_whatsapp_canal(mensagem_whatsapp, dados["imagem"])
            if ok:
                resultados.append("Canal")
            else:
                erros.append("Canal")

        # ── Telegram ──
        if enviar_tg:
            try:
                _run_async(enviar_telegram(mensagem_telegram, dados["imagem"]))
                resultados.append("Telegram")
            except Exception as e:
                print(f"[app] Erro Telegram: {e!r}")
                erros.append("Telegram")

        # Flash com resultado
        if resultados:
            destinos_ok = " + ".join(resultados)
            flash(f"✅ Oferta enviada com sucesso! ({destinos_ok})", "success")
        if erros:
            destinos_err = ", ".join(erros)
            flash(f"⚠️ Falha ao enviar para: {destinos_err}", "warning")

        return redirect("/")

    return render_template("index.html")


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
