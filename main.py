import logging
from flask import Flask, request, jsonify
from pymongo import MongoClient
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, MONGO_URI, ADMIN_USER_ID

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Configuration
client = MongoClient(MONGO_URI)
db = client["ZATHAIX"]
movies_collection = db["movies"]
users_collection = db["users"]

# Flask App for Web API
flask_app = Flask(__name__)

# Helper Functions
def register_user(user_id):
    """Register a user in MongoDB."""
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "favorites": [], "history": []})

def search_movies(query):
    """Search for movies in the database."""
    return list(movies_collection.find({"movie": {"$regex": query, "$options": "i"}}))

def add_to_favorites(user_id, movie_name):
    """Add a movie to the user's favorites."""
    users_collection.update_one({"user_id": user_id}, {"$addToSet": {"favorites": movie_name}})

def get_user_favorites(user_id):
    """Retrieve a user's favorite movies."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("favorites", []) if user else []

def add_to_history(user_id, query):
    """Add a query to the user's search history."""
    users_collection.update_one({"user_id": user_id}, {"$push": {"history": query}})

def get_user_history(user_id):
    """Retrieve a user's search history."""
    user = users_collection.find_one({"user_id": user_id})
    return user.get("history", []) if user else []

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler."""
    user_id = update.message.from_user.id
    register_user(user_id)

    keyboard = [
        [InlineKeyboardButton("⇆ Add Me To Your Group ⇆", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("Support Us", url="https://t.me/support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "Hello! I am **ZATHAIX**, your assistant for movies and series.\n\n"
        "**Owner:** Contact @YourUsername\n"
        "**Support:** [Telegram Support](https://t.me/support)\n"
        "**Help:** Type a movie title to search for it."
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle movie search queries."""
    query = update.message.text.strip().lower()
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
        movie_name = query.data.split("_")[1]
        movie = movies_collection.find_one({"movie": movie_name})
        if movie:
            text = (
                f"🎬 *{movie['movie']}*\n\n"
                f"**Genre**: {movie['genre']}\n"
                f"**Rating**: {movie['rating']}\n\n"
                f"[Download Here]({movie['Terabox']})"
            )
            keyboard = [
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_movies")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await query.message.reply_text("Movie not found.")

    elif query.data == "back_to_movies":
        # Example: Returning to a previous list of movies
        results = movies_collection.find().limit(10)  # Fetch movies
        keyboard = [[InlineKeyboardButton(movie["movie"], callback_data=f"movie_{movie['movie']}")] for movie in results]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("Select a movie:", reply_markup=reply_markup)

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's favorite movies."""
    user_id = update.message.from_user.id
    favorites = get_user_favorites(user_id)
    if favorites:
        await update.message.reply_text(f"Your favorites:\n{'\n'.join(favorites)}")
    else:
        await update.message.reply_text("You have no favorite movies yet!")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's search history."""
    user_id = update.message.from_user.id
    history = get_user_history(user_id)
    if history:
        await update.message.reply_text(f"Your search history:\n{'\n'.join(history)}")
    else:
        await update.message.reply_text("You have no search history yet!")

async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a list of all inline keyboard commands."""
    commands_text = (
        "Here are the available commands and their descriptions:\n\n"
        "- **Inline Commands:**\n"
        "  • `movie_<movie_name>`: Select a movie to view details.\n"
        "  • `back_to_movies`: Return to the movie list.\n"
        "\n- **Text Commands:**\n"
        "  • `/start`: Start the bot.\n"
        "  • `/commands`: Show this command list.\n"
        "  • `/f`: View your favorite movies.\n"
        "  • `/h`: View your search history.\n"
        "  • `/notify`: Admin command to notify all users."
    )

    await update.message.reply_text(commands_text, parse_mode="Markdown")

async def notify_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to notify all users."""
    user_id = update.message.from_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message = " ".join(context.args)
    users = users_collection.find()
    for user in users:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=message)
        except Exception as e:
            logging.warning(f"Failed to notify user {user['user_id']}: {e}")

    await update.message.reply_text("Notification sent to all users!")

# Flask Routes for Web API
@flask_app.route("/api/search", methods=["GET"])
def api_search():
    """Search for movies."""
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = search_movies(query)
    return jsonify(results)

@flask_app.route("/api/favorites", methods=["POST"])
def api_add_favorite():
    """Add a movie to the user's favorites."""
    data = request.json
    user_id = data.get("user_id")
    movie_name = data.get("movie")

    if not user_id or not movie_name:
        return jsonify({"error": "user_id and movie are required"}), 400

    add_to_favorites(user_id, movie_name)
    return jsonify({"message": f"'{movie_name}' added to favorites!"})

@flask_app.route("/api/history/<int:user_id>", methods=["GET"])
def api_get_history(user_id):
    """Get user search history."""
    history = get_user_history(user_id)
    return jsonify(history)

@flask_app.route("/api/notify", methods=["POST"])
def api_notify_users():
    """Notify all users from the web."""
    data = request.json
    message = data.get("message")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    users = users_collection.find()
    for user in users:
        try:
            application.bot.send_message(chat_id=user["user_id"], text=message)
        except Exception as e:
            logging.warning(f"Failed to notify user {user['user_id']}: {e}")

    return jsonify({"message": "Notification sent to all users!"})

# Run Flask and Telegram Bot
if __name__ == "__main__":
    from threading import Thread

    # Flask app in a separate thread
    flask_thread = Thread(target=lambda: flask_app.run(host="0.0.0.0", port=5000))
    flask_thread.start()

    # Telegram Bot
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("commands", show_commands))
    application.add_handler(CommandHandler("f", show_favorites))
    application.add_handler(CommandHandler("h", show_history))
    application.add_handler(CommandHandler("notify", notify_users))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()