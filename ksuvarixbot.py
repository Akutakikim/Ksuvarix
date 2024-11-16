import os
import logging
import json
import requests
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Manually set the bot token (replace with your actual token)
BOT_TOKEN = "7644485485:AAGKIOfpYqqleSEwMTpPbX-qt6UK3ROrr8Y"  # Replace this with your actual bot token

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global storage
links_db = {}
user_balances = {}  # Stores user balances

# Shared Ad Link
AD_LINK = "https://www.profitablecpmrate.com/uzg22nip?key=ccae44b301827327837f33862057bb05"

# Load links from the JSON file
def load_links():
    global links_db
    try:
        with open("/storage/emulated/0/telegram_bot/linksbot.json", "r") as file:  # Ensure the file is in the correct path
            links_db = json.load(file)
        logging.info("Links successfully loaded!")
    except Exception as e:
        logging.error(f"Failed to load links: {e}")

# Shorten URL using TinyURL
def shorten_url(url):
    try:
        response = requests.get(f"http://tinyurl.com/api-create.php?url={url}")
        if response.status_code == 200:
            return response.text
        else:
            return url
    except requests.RequestException as e:
        logging.error(f"Error shortening URL: {e}")
        return url

# Telegram bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Define the inline keyboard
    keyboard = [
        [InlineKeyboardButton("⇆ Add Me To Your Group ⇆", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [
            InlineKeyboardButton("Owner ©", callback_data="owner"),
            InlineKeyboardButton("Support", callback_data="support"),
        ],
        [
            InlineKeyboardButton("§ Help ∆", callback_data="help"),
            InlineKeyboardButton("€ About ¥", callback_data="about"),
        ],
        [InlineKeyboardButton("Join Terabox", url="https://www.nephobox.com/referral/4401514781831")],
        [InlineKeyboardButton("Watch Ad", url=AD_LINK), InlineKeyboardButton("Confirm Watch", callback_data="watch_ad")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # URL of the image to be sent
    image_url = "/storage/emulated/0/pictures/IMG_20241116_184338.png"  # Replace with your image URL

    # Send the image with the reply markup
    await update.message.reply_photo(
        photo=image_url,
        caption="Hello! I am your bot, here to provide movies and series. Add me to your group or chat with me privately!",
        reply_markup=reply_markup
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    balance = user_balances.get(user_id, 0)
    await update.message.reply_text(f"Your balance is: {balance} Zaruxcoin.")

async def watch_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Provide the ad link and reward Zaruxcoins after confirming the ad was watched
    user_id = str(update.message.from_user.id)
    current_balance = user_balances.get(user_id, 0)
    updated_balance = current_balance + 0.5
    user_balances[user_id] = updated_balance
    await update.message.reply_text(
        f"Watch the ad here: {AD_LINK}\n\nYou earned 0.5 Zaruxcoin! Your updated balance is {updated_balance} Zaruxcoin."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip().lower()
    movie_data = links_db.get(query)

    if movie_data:
        await send_movie_details(update, query, movie_data)
    else:
        await update.message.reply_text(
            f"Sorry, I couldn't find any links for '{query}'. Try searching for another movie!"
        )

async def send_movie_details(update: Update, title, movie_data):
    terabox_link = shorten_url(movie_data.get('Terabox', ''))
    poster_url = movie_data.get('Poster', '')

    response_text = f"Here is the download link for *{title}*:\n- [Terabox]({terabox_link})"

    if poster_url:
        await update.message.reply_photo(photo=poster_url, caption=response_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(response_text, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "owner":
        await query.edit_message_text("Contact the owner at @Uglyguy01.")
    elif query.data == "support":
        await query.edit_message_text("Support is available at https://t.me/KSUVARIXCOMINT.")
    elif query.data == "help":
        await query.edit_message_text(
            "Commands:\n"
            "- /start: Start interacting with the bot\n"
            "- /balance: Check your Zaruxcoin balance\n"
            "- /watch_ad: Earn Zaruxcoin by watching ads\n"
            "- Send a movie title to get download links and posters!"
        )
    elif query.data == "about":
        await query.edit_message_text("This bot is maintained by ZAFINIX STUDIOS.")
    elif query.data == "watch_ad":
        user_id = str(update.callback_query.from_user.id)
        current_balance = user_balances.get(user_id, 0)
        updated_balance = current_balance + 0.5
        user_balances[user_id] = updated_balance
        await query.edit_message_text(f"Thanks for watching the ad! You earned 0.5 Zaruxcoin. Your updated balance is {updated_balance} Zaruxcoin.")

# Set commands for the bot
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Start interacting with the bot"),
        BotCommand("balance", "Check your Zaruxcoin balance"),
        BotCommand("watch_ad", "Earn Zaruxcoin by watching ads"),
    ]
    await application.bot.set_my_commands(commands)

# Main function
if __name__ == "__main__":
    load_links()  # Load links from JSON file

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("watch_ad", watch_ad))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()
