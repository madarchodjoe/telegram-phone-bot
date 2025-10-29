import logging
import requests
import asyncio
import os
from telethon import TelegramClient, events

# --- Configuration ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Bot Token (hardcoded for Termux) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- API ID and API Hash ---
# Get these from https://my.telegram.org/apps
API_ID = int(os.getenv("API_ID"))  # Replace with your actual API ID (integer)
API_HASH = os.getenv("API_HASH")  # Replace with your actual API Hash (string)

if not API_ID or not API_HASH:
    logger.critical("!!! ERROR: API_ID and API_HASH must be set. Get them from https://my.telegram.org/apps !!!")
    exit()

# --- API Endpoint (no key required) ---
API_URL = "https://ox.taitaninfo.workers.dev/?mobile={number_to_lookup}"

# Create the bot client
bot = TelegramClient('bot_session', api_id=API_ID, api_hash=API_HASH)

# --- Bot Handlers ---

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Sends a welcome message when the /start command is issued."""
    user = await event.get_sender()
    user_name = user.first_name

    start_message = (
        f"Hi {user_name}!\n\n"
        f"Welcome to the Phone Number Bot. Just send me any "
        f"phone number and I'll try to find information about it.\n\n"
        f"— This bot was created by Rahul Sharma"
    )

    await event.reply(start_message)
    raise events.StopPropagation


@bot.on(events.NewMessage(pattern='^(?!/)'))
async def message_handler(event):
    """Handles any regular text message (that doesn't start with '/')"""
    phone_number = event.message.text.strip()
    chat_id = event.chat_id

    logger.info(f"Received number: {phone_number} from chat_id: {chat_id}")

    async with bot.action(chat_id, 'typing'):
        try:
            # --- Call the API ---
            url = API_URL.format(number_to_lookup=phone_number)
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            logger.info(f"API Response: {data}")

            # --- Format the reply ---
            if data.get("error"):
                await event.reply(f"Error: {data['error']}")
                return

            reply_message = f"<b>Info for {phone_number}:</b>\n"
            info_found = False

            for key, value in data.items():
                if value and str(value).strip() not in ["", "NA", "N/A"]:
                    formatted_key = key.replace("_", " ").title()
                    reply_message += f"\n<b>{formatted_key}:</b> {value}"
                    info_found = True

            if not info_found:
                await event.reply(f"No details found for {phone_number}.")
            else:
                await event.reply(reply_message, parse_mode='html')

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            await event.reply("The API service seems to be down. Please try again later.")

        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
            await event.reply("I'm having trouble connecting to the API.")

        except Exception as e:
            logger.error(f"An unknown error occurred: {e}")
            await event.reply("An unexpected error happened. I've logged it.")


async def main():
    """Start the bot."""
    logger.info("Bot started (Telethon)...")
    await bot.start(bot_token=BOT_TOKEN)
    await bot.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
