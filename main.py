import logging
from flask import Flask, jsonify, request
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread

# Bot and Database Configuration
BOT_TOKEN = "7652316281:AAH84LXEvmq1GO365vRx8FWhJG2Jz4SydL0"
MONGO_URI = "mongodb+srv://Zafinet:<Akik20f20varb04>@zafinet.wftow.mongodb.net/?retryWrites=true&w=majority&appName=Zafinet"
ADMIN_USER_ID = 5912828707  # Replace with your admin Telegram user ID
BOT_VERSION = "ZATHAIX Bot v-1.3.12"

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Configuration
client = MongoClient(MONGO_URI)
db = client["ZATHAIX"]
movies_collection = db["movies"]
users_collection = db["users"]

# Flask App for API
flask_app = Flask(__name__)

# Helper Functions
def register_user(user_id):
    """Register a user if not already registered."""
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "favorites": [], "history": []})

def search_movies(query):
    """Search for movies in the database."""
    return list(movies_collection.find({"movie": {"$regex": query, "$options": "i"}}))

def add_to_favorites(user_id, movie_name):
    """Add a movie to user's favorites."""
    users_collection.update_one({"user_id": user_id}, {"$addToSet": {"favorites": movie_name}})

def get_user_favorites(user_id):
    """Retrieve user's favorite movies."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("favorites", []) if user else []

def add_to_history(user_id, query):
    """Add a search query to user's history."""
    users_collection.update_one({"user_id": user_id}, {"$push": {"history": query}})

def get_user_history(user_id):
    """Retrieve user's search history."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("history", []) if user else []

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user_id = update.message.from_user.id
    register_user(user_id)

    keyboard = [
        [InlineKeyboardButton("⇆ Add Me To Your Group ⇆", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("Support Us", url="https://t.me/support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"Hello! I am **{BOT_VERSION}**, your assistant for movies and series.\n\n"
        "**Owner:** Contact @YourUsername\n"
        "**Support:** [Telegram Support](https://t.me/support)\n"
        "**Help:** Type a movie title to search for it."
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle movie search queries."""
    query = update.message.text.strip()
    user_id = update.message.from_user.id
    register_user(user_id)
    add_to_history(user_id, query)

    results = search_movies(query)
    if results:
        keyboard = [
            [InlineKeyboardButton(movie["movie"], callback_data=f"movie_{movie['movie']}")] for movie in results[:10]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Found {len(results)} results for '{query}'. Select a movie:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("No results found for your query.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data.startswith("movie_"):
        movie_name = query.data.split("_", 1)[1]
        movie = movies_collection.find_one({"movie": movie_name})
        if movie:
            text = (
                f"🎬 *{movie['movie']}*\n\n"
                f"**Genre**: {movie['genre']}\n"
                f"**Rating**: {movie['rating']}\n\n"
                f"[Download Here]({movie['Terabox']})"
            )
            await query.message.edit_text(text, parse_mode="Markdown")
        else:
            await query.message.edit_text("Movie not found.")
    else:
        await query.message.edit_text("Invalid action.")

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's favorite movies."""
    user_id = update.message.from_user.id
    favorites = get_user_favorites(user_id)
    if favorites:
        await update.message.reply_text("Your favorite movies:\n" + "\n".join(favorites))
    else:
        await update.message.reply_text("You have no favorite movies yet!")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's search history."""
    user_id = update.message.from_user.id
    history = get_user_history(user_id)
    if history:
        await update.message.reply_text("Your search history:\n" + "\n".join(history))
    else:
        await update.message.reply_text("You have no search history yet!")

async def notify_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Notify all users (admin-only command)."""
    user_id = update.message.from_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Please provide a message to notify users.")
        return

    users = users_collection.find()
    for user in users:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=message)
        except Exception as e:
            logging.warning(f"Failed to send message to user {user['user_id']}: {e}")
    await update.message.reply_text("Notification sent to all users.")

# Flask Route Example
@flask_app.route("/")
def home():
    return jsonify({"status": "Bot and API are running", "version": BOT_VERSION})

# Main Bot Runner
if __name__ == "__main__":
    # Run Flask App in a Separate Thread
    flask_thread = Thread(target=lambda: flask_app.run(host="0.0.0.0", port=5000))
    flask_thread.start()

    # Run Telegram Bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("f", show_favorites))
    application.add_handler(CommandHandler("h", show_history))
    application.add_handler(CommandHandler("notify", notify_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()
