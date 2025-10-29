import logging
import requests
import asyncio
import os
from telethon import TelegramClient, events

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
API_URL = "https://ox.taitaninfo.workers.dev/?mobile={number_to_lookup}"

# --- Initialize Bot ---
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- /start Command ---
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Welcome message"""
    await event.reply(
        "👋 <b>Hey there!</b>\n\n"
        "Welcome to <b>📞 Number Info Bot</b>!\n\n"
        "Just send me a phone number (max 13 digits), and I’ll find public info about it.\n\n"
        "Example:\n<code>918123456789</code>\n\n"
        "— Created by Rahul Sharma 💻",
        parse_mode='html'
    )

# --- Message Handler ---
@bot.on(events.NewMessage(pattern='^(?!/)'))
async def message_handler(event):
    """Handle number lookup"""
    if event.out or event.sender_id == (await bot.get_me()).id:
        return

    phone_number = event.message.text.strip()
    chat_id = event.chat_id

    if not phone_number.isdigit() or len(phone_number) > 13:
        await event.reply("⚠️ Please send a valid phone number (digits only, up to 13).")
        return

    logger.info(f"Received number: {phone_number}")

    async with bot.action(chat_id, 'typing'):
        try:
            response = requests.get(API_URL.format(number_to_lookup=phone_number))
            response.raise_for_status()
            data = response.json()
            logger.info(f"API Response: {data}")

            if data.get("error"):
                await event.reply(f"❌ <b>Error:</b> {data['error']}", parse_mode='html')
                return

            emoji_map = {
                "name": "🧍‍♂️",
                "carrier": "📡",
                "country": "🌍",
                "city": "🏙️",
                "address": "📍",
                "line_type": "📞",
                "status": "✅",
                "email": "✉️",
                "gender": "🚻",
                "dob": "🎂"
            }

            info_lines = []
            for key, value in data.items():
                if value and str(value).strip() not in ["", "NA", "N/A"]:
                    emoji = emoji_map.get(key.lower(), "🔹")
                    formatted_key = key.replace("_", " ").title()
                    info_lines.append(f"{emoji} {formatted_key}: {value}")

            if not info_lines:
                await event.reply("😕 No information found for this number.")
                return

            # Box-style formatted reply
            reply_message = (
                f"```\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📱 Number Info Lookup\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Number: {phone_number}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{chr(10).join(info_lines)}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔍 Data fetched via API\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"```"
            )

            await event.reply(reply_message, parse_mode='markdown')

        except requests.exceptions.RequestException as e:
            logger.error(f"API Error: {e}")
            await event.reply("⚠️ The lookup service is currently unavailable. Please try again later.")
        except Exception as e:
            logger.error(f"Unexpected Error: {e}")
            await event.reply("❗ An unexpected error occurred. Please try again later.")

# --- Run Bot ---
def main():
    logger.info("🤖 Bot is running...")
    bot.run_until_disconnected()

if __name__ == "__main__":
    main()
