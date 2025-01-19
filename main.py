from flask import Flask, request, jsonify, render_template, redirect, url_for

# Flask App Configuration
app = Flask(__name__)

# In-memory data storage
users = {}  # {user_id: {"favorites": [], "history": []}}
movies = [
    {"title": "Inception", "genre": "Sci-Fi", "rating": "8.8", "download_link": "http://example.com/inception"},
    {"title": "The Matrix", "genre": "Action", "rating": "8.7", "download_link": "http://example.com/matrix"},
    {"title": "Interstellar", "genre": "Sci-Fi", "rating": "8.6", "download_link": "http://example.com/interstellar"},
]

# Helper Functions
def register_user(user_id):
    """Register a new user."""
    if user_id not in users:
        users[user_id] = {"favorites": [], "history": []}

def search_movies(query):
    """Search for movies in the database."""
    return [movie for movie in movies if query.lower() in movie["title"].lower()]

def add_to_favorites(user_id, movie_title):
    """Add a movie to user's favorites."""
    if user_id in users:
        users[user_id]["favorites"].append(movie_title)

def get_user_favorites(user_id):
    """Retrieve user's favorite movies."""
    return users[user_id]["favorites"] if user_id in users else []

def add_to_history(user_id, query):
    """Add a search query to user's history."""
    if user_id in users:
        users[user_id]["history"].append(query)

def get_user_history(user_id):
    """Retrieve user's search history."""
    return users[user_id]["history"] if user_id in users else []

# Routes
@app.route("/")
def home():
    """Home page."""
    return render_template("home.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    """Search for movies."""
    if request.method == "POST":
        user_id = request.form.get("user_id")
        query = request.form.get("query")
        register_user(user_id)
        add_to_history(user_id, query)
        results = search_movies(query)
        return render_template("search_results.html", results=results, query=query, user_id=user_id)
    return render_template("search.html")

@app.route("/favorites/<user_id>")
def favorites(user_id):
    """Show user's favorite movies."""
    register_user(user_id)
    favorites = get_user_favorites(user_id)
    return render_template("favorites.html", favorites=favorites, user_id=user_id)

@app.route("/history/<user_id>")
def history(user_id):
    """Show user's search history."""
    register_user(user_id)
    history = get_user_history(user_id)
    return render_template("history.html", history=history, user_id=user_id)

@app.route("/add_to_favorites", methods=["POST"])
def add_to_favorites_route():
    """Add a movie to favorites."""
    user_id = request.form.get("user_id")
    movie_title = request.form.get("movie_title")
    add_to_favorites(user_id, movie_title)
    return redirect(url_for("favorites", user_id=user_id))

# Templates
templates = {
    "home.html": """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Movie Bot</title>
    </head>
    <body>
        <h1>Welcome to Movie Bot</h1>
        <a href="/search">Search for Movies</a><br>
        <form action="/favorites/<user_id>" method="get">
            <label for="user_id">Enter Your User ID:</label>
            <input type="text" name="user_id" required>
            <button type="submit">View Favorites</button>
        </form>
        <form action="/history/<user_id>" method="get">
            <label for="user_id">Enter Your User ID:</label>
            <input type="text" name="user_id" required>
            <button type="submit">View History</button>
        </form>
    </body>
    </html>
    """,
    "search.html": """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Movies</title>
    </head>
    <body>
        <h1>Search for Movies</h1>
        <form method="post">
            <label for="user_id">User ID:</label>
            <input type="text" name="user_id" required><br>
            <label for="query">Search Query:</label>
            <input type="text" name="query" required><br>
            <button type="submit">Search</button>
        </form>
    </body>
    </html>
    """,
    "search_results.html": """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results</title>
    </head>
    <body>
        <h1>Results for "{{ query }}"</h1>
        {% if results %}
            <ul>
            {% for movie in results %}
                <li>
                    {{ movie.title }} - {{ movie.genre }} - {{ movie.rating }}
                    <form method="post" action="/add_to_favorites">
                        <input type="hidden" name="user_id" value="{{ user_id }}">
                        <input type="hidden" name="movie_title" value="{{ movie.title }}">
                        <button type="submit">Add to Favorites</button>
                    </form>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No movies found.</p>
        {% endif %}
    </body>
    </html>
    """,
    "favorites.html": """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Favorites</title>
    </head>
    <body>
        <h1>Your Favorites</h1>
        {% if favorites %}
            <ul>
            {% for movie in favorites %}
                <li>{{ movie }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No favorites yet.</p>
        {% endif %}
    </body>
    </html>
    """,
    "history.html": """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search History</title>
    </head>
    <body>
        <h1>Your Search History</h1>
        {% if history %}
            <ul>
            {% for query in history %}
                <li>{{ query }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No history yet.</p>
        {% endif %}
    </body>
    </html>
    """,
}

# Dynamically serve templates
@app.route("/template/<template_name>")
def get_template(template_name):
    return templates.get(template_name, "Template not found")

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
