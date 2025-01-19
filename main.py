import logging
from flask import Flask, request, jsonify

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

# In-memory storage (for simplicity, replace with a database later if needed)
movies = [
    {"movie": "Inception", "genre": "Sci-Fi", "rating": "8.8", "download_link": "https://example.com/inception"},
    {"movie": "The Matrix", "genre": "Action/Sci-Fi", "rating": "8.7", "download_link": "https://example.com/matrix"},
    {"movie": "Interstellar", "genre": "Sci-Fi/Drama", "rating": "8.6", "download_link": "https://example.com/interstellar"},
]
users = {}

# Helper functions
def register_user(user_id):
    if user_id not in users:
        users[user_id] = {"favorites": [], "history": []}

# Routes
@app.route("/")
def home():
    return jsonify({"status": "Backend is running", "message": "Welcome to the Movie Search API!"})

@app.route("/search", methods=["GET"])
def search_movies():
    query = request.args.get("query", "").strip()
    user_id = request.args.get("user_id")
    
    if not query or not user_id:
        return jsonify({"error": "Missing query or user_id"}), 400
    
    register_user(user_id)
    users[user_id]["history"].append(query)
    
    results = [movie for movie in movies if query.lower() in movie["movie"].lower()]
    if results:
        return jsonify({"results": results})
    return jsonify({"message": "No movies found"}), 404

@app.route("/favorites", methods=["GET", "POST"])
def manage_favorites():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    register_user(user_id)
    
    if request.method == "POST":
        movie_name = request.json.get("movie")
        if not movie_name:
            return jsonify({"error": "Missing movie name"}), 400
        
        users[user_id]["favorites"].append(movie_name)
        return jsonify({"message": f"'{movie_name}' added to favorites"})
    
    return jsonify({"favorites": users[user_id]["favorites"]})

@app.route("/history", methods=["GET"])
def get_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    register_user(user_id)
    return jsonify({"history": users[user_id]["history"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
