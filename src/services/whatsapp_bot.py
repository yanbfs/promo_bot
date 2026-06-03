import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from src.config.config import WHATSAPP_PERFIL, WHATSAPP_GRUPO, WHATSAPP_CANAL
from src.utils import copiar_texto_para_clipboard, copiar_imagem_para_clipboard

_driver = None


# ── Driver ────────────────────────────────────────────────────────────────────

def ensure_driver():
    global _driver
    if _driver is not None:
        try:
            _ = _driver.current_url
            return
        except WebDriverException:
            try:
                _driver.quit()
            except Exception:
                pass
            _driver = None
        except Exception:
            try:
                _driver.quit()
            except Exception:
                pass
            _driver = None

    chromedriver_autoinstaller.install()
    opts = Options()
    opts.add_argument(f"--user-data-dir={WHATSAPP_PERFIL}")
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("detach", True)

    _driver = webdriver.Chrome(options=opts)
    _driver.get("https://web.whatsapp.com")

    print("[WhatsApp] Aguardando carregamento...")
    while True:
        try:
            _driver.find_element(By.XPATH, '//button[@aria-label="Conversas"]')
            break
        except Exception:
            time.sleep(1)
    print("[WhatsApp] Pronto.")


# ══════════════════════════════════════════════════════════════════════════════
# GRUPO — navegação
# ══════════════════════════════════════════════════════════════════════════════

def _clicar_aba_conversas():
    """Garante que a aba Conversas está ativa (necessário ao voltar do canal)."""
    seletores = [
        '//button[@aria-label="Conversas"]',
        '//button[@data-navbar-item-index="0"]',
    ]
    for sel in seletores:
        try:
            btn = _driver.find_element(By.XPATH, sel)
            _driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.8)
            return True
        except Exception:
            continue
    return False


def _find_search_global():
    """Barra de pesquisa principal (aba Conversas)."""
    seletores = [
        '//*[@data-tab="3"]',
        '//input[@placeholder="Pesquisar ou começar uma nova conversa"]',
        '//div[@contenteditable="true" and @data-tab="3"]',
        '//div[@contenteditable="true" and contains(@aria-label,"Pesquisar")]',
    ]
    for sel in seletores:
        try:
            return _driver.find_element(By.XPATH, sel)
        except Exception:
            continue
    return None


def _select_conversation(title, timeout=8):
    """Clica no grupo com o título especificado."""
    end = time.time() + timeout
    xpaths = [
        f'//span[@title="{title}"]',
        f'//div[@title="{title}"]',
        f'//span[contains(@title,"{title}")]',
        f'//div[contains(@title,"{title}")]',
    ]
    while time.time() < end:
        for xp in xpaths:
            try:
                el = _driver.find_element(By.XPATH, xp)
                try:
                    el.click()
                except Exception:
                    _driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                continue
        time.sleep(0.25)
    return False


# ══════════════════════════════════════════════════════════════════════════════
# CANAL — navegação
# ══════════════════════════════════════════════════════════════════════════════

def _clicar_aba_canais():
    """Clica no botão 'Canais' na navbar lateral."""
    seletores = [
        '//button[@aria-label="Canais"]',
        '//button[@data-navbar-item-index="2"]',
    ]
    for sel in seletores:
        try:
            btn = _driver.find_element(By.XPATH, sel)
            _driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            return True
        except Exception:
            continue
    print("[WhatsApp] Botão 'Canais' não encontrado.")
    return False


def _find_search_canais():
    """Campo de pesquisa dentro do painel de Canais."""
    seletores = [
        '//div[@data-testid="newsletter-tab-drawer"]//input[@aria-label="Pesquisar"]',
        '//div[@aria-label="Guia da aba Canal"]//input[@type="text"]',
        '//div[@data-testid="newsletter-tab-drawer"]//input[@type="text"]',
    ]
    for sel in seletores:
        try:
            return _driver.find_element(By.XPATH, sel)
        except Exception:
            continue
    return None


def _select_canal(nome_canal, timeout=8):
    """Clica no item do canal com o nome especificado."""
    end = time.time() + timeout
    xpaths = [
        f'//div[@aria-label="Canal {nome_canal}"]',
        f'//div[@data-testid="newsletter-tab-newsletter-cell" and @aria-label="Canal {nome_canal}"]',
        f'//span[@dir="auto" and @title="{nome_canal}"]',
        f'//span[@dir="auto" and contains(@title,"{nome_canal}")]',
    ]
    while time.time() < end:
        for xp in xpaths:
            try:
                el = _driver.find_element(By.XPATH, xp)
                try:
                    el.click()
                except Exception:
                    _driver.execute_script("arguments[0].click();", el)
                return True
            except Exception:
                continue
        time.sleep(0.25)
    return False


# ══════════════════════════════════════════════════════════════════════════════
# Elementos de input — compartilhados entre grupo e canal
# ══════════════════════════════════════════════════════════════════════════════

def _find_message_input():
    seletores = [
        '//div[@contenteditable="true" and @data-tab="10"]',
        '//div[@contenteditable="true" and @data-lexical-editor="true" and @data-tab="10"]',
        '//div[@contenteditable="true" and contains(@aria-label,"mensagem") and @data-tab="10"]',
        '//div[@contenteditable="true" and @role="textbox" and @data-tab="10"]',
    ]
    for sel in seletores:
        try:
            return _driver.find_element(By.XPATH, sel)
        except Exception:
            continue
    return None


def _find_preview_caption():
    """Campo de legenda do modal de preview de imagem (data-tab='undefined')."""
    seletores = [
        '//div[@data-testid="media-caption-input-container"]',
        '//div[@contenteditable="true" and @data-lexical-editor="true" and @data-tab="undefined"]',
        '//div[@contenteditable="true" and @aria-placeholder="Digite uma atualização" and not(@data-tab="10")]',
        '//div[contains(@class,"lexical-rich-text-input")]//div[@contenteditable="true" and not(@data-tab="10")]',
    ]
    for sel in seletores:
        try:
            el = _driver.find_element(By.XPATH, sel)
            if el.get_attribute("data-tab") != "10":
                return el
        except Exception:
            continue
    return None


def _find_send_button():
    seletores = [
        '//div[@aria-label="Enviar 1 item selecionado" and @role="button"]',
        '//div[@aria-label="Enviar" and @role="button"]',
        '//span[@data-icon="wds-ic-send-filled"]/ancestor::div[@role="button"]',
        '//*[@aria-label="Enviar"]',
    ]
    for sel in seletores:
        try:
            return _driver.find_element(By.XPATH, sel)
        except Exception:
            continue
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Utilitários de interação
# ══════════════════════════════════════════════════════════════════════════════

def _focar(elemento):
    try:
        _driver.execute_script("arguments[0].focus();", elemento)
    except Exception:
        try:
            elemento.click()
        except Exception:
            pass


def _limpar_campo(elemento):
    """Apaga todo o conteúdo de um campo (input ou contenteditable)."""
    try:
        elemento.clear()
    except Exception:
        pass
    try:
        _focar(elemento)
        ActionChains(_driver)\
            .key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL)\
            .send_keys(Keys.DELETE)\
            .perform()
    except Exception:
        pass
    time.sleep(0.15)


def _colar_texto(elemento, texto: str):
    texto_limpo = ''.join(
        ch for ch in texto
        if ch in ('\n', '\t') or (ord(ch) >= 32 and ord(ch) != 0xFEFF)
    )
    copiar_texto_para_clipboard(texto_limpo)
    try:
        elemento.send_keys(Keys.CONTROL, 'v')
    except Exception:
        ActionChains(_driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
    time.sleep(0.3)


def _enviar_imagem_com_legenda(img_url: str, legenda: str) -> bool:
    copiar_imagem_para_clipboard(img_url)
    campo = _find_message_input()
    if not campo:
        print("[WhatsApp] Campo de input não encontrado.")
        return False

    _focar(campo)
    ActionChains(_driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
    print("[WhatsApp] Imagem colada, aguardando preview...")
    time.sleep(3)

    preview = _find_preview_caption()
    if not preview:
        print("[WhatsApp] Campo de legenda não encontrado — enviando sem legenda.")
        botao = _find_send_button()
        if botao:
            _driver.execute_script("arguments[0].click();", botao)
        return False

    _focar(preview)
    time.sleep(0.3)
    _colar_texto(preview, legenda)
    time.sleep(0.5)

    botao = _find_send_button()
    if botao:
        _driver.execute_script("arguments[0].click();", botao)
        print("[WhatsApp] Imagem + legenda enviadas.")
    else:
        print("[WhatsApp] Botão Enviar não encontrado, tentando Enter.")
        preview.send_keys(Keys.ENTER)

    time.sleep(3)
    return True


def _enviar_somente_texto(texto: str) -> bool:
    campo = _find_message_input()
    if not campo:
        print("[WhatsApp] Campo de input não encontrado.")
        return False

    _focar(campo)
    time.sleep(0.3)
    _colar_texto(campo, texto)
    time.sleep(0.5)
    campo.send_keys(Keys.ENTER)
    time.sleep(2)
    print("[WhatsApp] Texto enviado.")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# Pontos de entrada públicos
# ══════════════════════════════════════════════════════════════════════════════

def enviar_whatsapp_grupo(mensagem: str, img_url: str | None = None) -> bool:
    """Navega até o grupo via barra de pesquisa principal e envia."""
    global _driver
    try:
        ensure_driver()
        print(f"[WhatsApp] Enviando para o grupo '{WHATSAPP_GRUPO}'...")

        _clicar_aba_conversas()

        search = _find_search_global()
        if search:
            _focar(search)
            try:
                search.clear()
            except Exception:
                ActionChains(_driver).click(search)\
                    .key_down(Keys.CONTROL).send_keys('a')\
                    .key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
            time.sleep(0.15)
            search.send_keys(WHATSAPP_GRUPO)
            time.sleep(0.8)

        if not _select_conversation(WHATSAPP_GRUPO, timeout=6):
            print(f"[WhatsApp] Grupo '{WHATSAPP_GRUPO}' não encontrado.")
            return False

        time.sleep(0.4)

        if img_url:
            ok = _enviar_imagem_com_legenda(img_url, mensagem)
        else:
            ok = _enviar_somente_texto(mensagem)

        # Limpa a barra de pesquisa do grupo após o envio
        search = _find_search_global()
        if search:
            _limpar_campo(search)
            print("[WhatsApp] Barra de pesquisa do grupo limpa.")

        return ok

    except Exception as e:
        print(f"[WhatsApp] Erro no grupo: {e!r}")
        return False


def enviar_whatsapp_canal(mensagem: str, img_url: str | None = None) -> bool:
    """Navega até o canal via aba Canais e envia."""
    global _driver
    try:
        ensure_driver()
        print(f"[WhatsApp] Enviando para o canal '{WHATSAPP_CANAL}'...")

        if not _clicar_aba_canais():
            print("[WhatsApp] Não foi possível abrir o painel de Canais.")
            return False

        time.sleep(1)

        search = _find_search_canais()
        if search:
            _focar(search)
            try:
                search.clear()
            except Exception:
                ActionChains(_driver).click(search)\
                    .key_down(Keys.CONTROL).send_keys('a')\
                    .key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
            time.sleep(0.15)
            search.send_keys(WHATSAPP_CANAL)
            time.sleep(1)
        else:
            print("[WhatsApp] Barra de pesquisa de canais não encontrada.")

        if not _select_canal(WHATSAPP_CANAL, timeout=6):
            print(f"[WhatsApp] Canal '{WHATSAPP_CANAL}' não encontrado.")
            return False

        time.sleep(0.8)

        if img_url:
            ok = _enviar_imagem_com_legenda(img_url, mensagem)
        else:
            ok = _enviar_somente_texto(mensagem)

        # Limpa a barra de pesquisa do canal após o envio
        search = _find_search_canais()
        if search:
            _limpar_campo(search)
            print("[WhatsApp] Barra de pesquisa do canal limpa.")

        return ok

    except Exception as e:
        print(f"[WhatsApp] Erro no canal: {e!r}")
        return False
