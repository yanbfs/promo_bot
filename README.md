# 🔥 Promo_Bot

Bot de automação para disparo de ofertas e promoções via **WhatsApp** (Grupo e Canal) e **Telegram**, com geração de mensagens por Inteligência Artificial.

---

## 📋 Sumário

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como Usar](#como-usar)
- [Como Funciona](#como-funciona)
- [Observações Importantes](#observações-importantes)

---

## Visão Geral

O **Promo_Bot** é uma aplicação web local construída com **Flask** que permite disparar promoções de produtos de forma rápida e automatizada. Basta preencher um formulário com os dados da oferta e o bot:

1. Gera uma mensagem promocional técnica e formatada usando **GPT-4o mini**
2. Envia a mensagem com imagem no **Grupo do WhatsApp** (via Selenium)
3. Envia a mensagem com imagem no **Canal do WhatsApp** (via Selenium)
4. Envia a mensagem com imagem no **Telegram** (via API oficial)

Cada destino pode ser ativado ou desativado individualmente direto no formulário.

---

## Funcionalidades

- ✅ Interface web simples e responsiva para preenchimento da oferta
- ✅ Geração automática de nome e descrição técnica do produto via IA
- ✅ Formatação automática de preço em Real (R$)
- ✅ Suporte a cupom de desconto (formatação específica por plataforma)
- ✅ Suporte a observação adicional (ex: frete grátis)
- ✅ Envio de imagem com legenda no WhatsApp (Grupo e Canal)
- ✅ Envio de foto com legenda no Telegram
- ✅ Seleção de destinos via checkboxes — envie só onde quiser
- ✅ Rodapé dinâmico com links de grupo, canal e Telegram (exibe só os que estiverem configurados)
- ✅ Retry automático com backoff exponencial nas chamadas à API da OpenAI
- ✅ Driver do Chrome mantido vivo entre envios (sem reabrir o navegador)
- ✅ Limpeza automática das barras de pesquisa após cada envio

---

## Estrutura do Projeto

```
Promo_Bot/
│
├── src/
│   ├── ai/
│   │   ├── ai_service.py          # Wrapper da API OpenAI com retry exponencial
│   │   └── message_processor.py   # Geração e montagem da mensagem final
│   │
│   ├── config/
│   │   └── config.py              # Leitura das variáveis de ambiente (.env)
│   │
│   ├── services/
│   │   ├── telegram_bot.py        # Envio via python-telegram-bot
│   │   └── whatsapp_bot.py        # Automação do WhatsApp Web via Selenium
│   │
│   └── utils.py                   # Download de imagem, clipboard (Windows)
│
├── templates/
│   └── index.html                 # Interface web do formulário
│
├── whatsapp_app/                  # Perfil do Chrome com sessão do WhatsApp Web
│                                  # (não versionado — ver .gitignore)
│
├── app.py                         # Aplicação Flask principal
├── .env                           # Variáveis de ambiente (não versionado)
├── env.example                    # Modelo do .env
├── requirements.txt               # Dependências Python
├── .gitignore
└── README.md
```

---

## Pré-requisitos

- **Python** 3.10 ou superior
- **Windows** (o envio via WhatsApp usa `pywin32` para manipular o clipboard)
- **Google Chrome** instalado
- Conta no **WhatsApp Web** já logada na pasta `whatsapp_app/`
- Conta e bot criado no **Telegram** (via [@BotFather](https://t.me/BotFather))
- Chave de API da **OpenAI** com acesso ao GPT-4o mini

---

## Instalação

**1. Clone o repositório**

```bash
git clone https://github.com/seu-usuario/Promo_Bot.git
cd Promo_Bot
```

**2. Crie e ative um ambiente virtual**

```bash
python -m venv venv
venv\Scripts\activate
```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

**4. Configure o arquivo `.env`**

```bash
cp env.example .env
```

Edite o `.env` com seus dados (veja a seção [Configuração](#configuração)).

**5. Faça o login do WhatsApp Web**

Na primeira execução, o Chrome abrirá o WhatsApp Web pedindo o QR Code. Após escanear, feche o navegador — a sessão fica salva na pasta `whatsapp_app/` e não precisará fazer login novamente.

---

## Configuração

Edite o arquivo `.env` na raiz do projeto:

```env
# ── OpenAI ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...

# ── Telegram ───────────────────────────────────────────────────────────────
TELEGRAM_TOKEN=123456:ABC...       # Token do bot gerado pelo @BotFather
TELEGRAM_CHAT_ID=-100123456789     # ID do canal/grupo do Telegram

# ── WhatsApp (Selenium) ────────────────────────────────────────────────────
WHATSAPP_GRUPO=Nome Exato do Grupo     # Nome do grupo exatamente como no app
WHATSAPP_CANAL=Nome Exato do Canal     # Nome do canal exatamente como no app
WHATSAPP_PERFIL=D:/LOJA/AgilityPromo/whatsapp_app  # Pasta do perfil Chrome

# ── Links do rodapé da mensagem ────────────────────────────────────────────
# Deixe em branco ou remova a linha para não exibir aquele link na mensagem
LINK_WHATSAPP=https://chat.whatsapp.com/...
LINK_WHATSAPP_CANAL=https://whatsapp.com/channel/...
LINK_TELEGRAM=https://t.me/...
```

### Sobre os links do rodapé

O rodapé da mensagem é montado **dinamicamente**: apenas os links que estiverem preenchidos no `.env` serão exibidos. Exemplos:

- Todos preenchidos:
  ```
  ⚡️ Entre nos grupos!
  👉 Grupo do WhatsApp: https://chat.whatsapp.com/...
  👉 Canal do WhatsApp: https://whatsapp.com/channel/...
  👉 Telegram: https://t.me/...
  ```

- Apenas Telegram preenchido:
  ```
  ⚡️ Entre nos grupos!
  👉 Telegram: https://t.me/...
  ```

- Nenhum preenchido: o bloco inteiro não aparece na mensagem.

---

## Como Usar

**1. Inicie o servidor**

```bash
python app.py
```

**2. Acesse no navegador**

```
http://localhost:5000
```

**3. Preencha o formulário**

| Campo | Obrigatório | Descrição |
|---|---|---|
| Nome do produto | ✅ | Nome original do produto |
| Preço | ✅ | Ex: `R$ 899,99` ou `89999` |
| Link afiliado | ✅ | URL do produto |
| URL da imagem | ✅ | Link direto para a imagem |
| Descrição técnica | ✅ | Descrição original — a IA reescreve |
| Cupom | ❌ | Código do cupom de desconto |
| Observação | ❌ | Ex: "Frete grátis para Sul e Sudeste" |

**4. Selecione os destinos**

Marque onde a oferta deve ser enviada:

- 📱 **Grupo** — Grupo do WhatsApp
- 📢 **Canal** — Canal do WhatsApp
- ✈️ **Telegram** — Canal/Grupo do Telegram

**5. Clique em "🚀 Gerar e Enviar"**

O bot irá gerar a mensagem com IA e disparar nos destinos selecionados. Um overlay de carregamento exibe o progresso em tempo real.

---

## Como Funciona

### Geração da mensagem (IA)

O `message_processor.py` chama o **GPT-4o mini** com um prompt técnico que:
- Reescreve o nome do produto adicionando emojis
- Gera uma descrição objetiva baseada apenas em especificações reais
- Proíbe explicitamente linguagem emocional e clichês de marketing

Em caso de falha na API, há até **3 tentativas** com backoff exponencial (1s → 2s → 4s → até 60s).

### Envio no WhatsApp (Selenium)

O `whatsapp_bot.py` controla o **Chrome** com um perfil persistente (sessão salva):

**Fluxo para o Grupo:**
1. Clica na aba "Conversas"
2. Pesquisa o grupo pelo nome na barra de pesquisa global
3. Clica no grupo
4. Cola a imagem via clipboard (`win32clipboard`)
5. Aguarda o modal de preview abrir
6. Cola a legenda no campo do modal
7. Clica em Enviar
8. Limpa a barra de pesquisa

**Fluxo para o Canal:**
1. Clica na aba "Canais"
2. Pesquisa o canal na barra de pesquisa interna do painel
3. Clica no canal
4. Segue o mesmo fluxo de imagem + legenda
5. Limpa a barra de pesquisa

### Envio no Telegram

O `telegram_bot.py` usa a biblioteca `python-telegram-bot` (assíncrona). Baixa a imagem, redimensiona para JPEG e envia como foto com legenda em formato **HTML** (para suporte a `<code>` no cupom).

---

## Observações Importantes

> **⚠️ Somente Windows**
> O envio via WhatsApp depende de `pywin32` para copiar imagem e texto para o clipboard do sistema. Não funciona em Linux ou macOS sem adaptação.

> **⚠️ WhatsApp Web deve estar logado**
> O perfil do Chrome em `whatsapp_app/` precisa ter a sessão do WhatsApp Web ativa. Se deslogar, basta abrir o Chrome manualmente nessa pasta e escanear o QR Code novamente.

> **⚠️ Não feche o Chrome durante o envio**
> O driver é mantido vivo entre envios (`detach: True`). Fechar o Chrome manualmente enquanto o bot estiver enviando pode causar erros.

> **⚠️ Seletores do WhatsApp Web**
> A interface do WhatsApp Web muda com atualizações. Se o bot parar de encontrar elementos, os seletores XPath em `whatsapp_bot.py` podem precisar de ajuste.
