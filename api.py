from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS, cross_origin
import mysql.connector
import logging
import requests
from datetime import datetime
from urllib.parse import unquote

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Telegram Bot Token (Keep this secure)
TELEGRAM_TOKEN = "7413982607:AAG09tBv0Pu2hJvetybPxi4WceSJnT4sJ9o" # Replace with your actual token

def get_db_connection():
    """Establish and return a MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="djmovie",
            autocommit=True
        )
        return connection
    except mysql.connector.Error as err:
        logger.error(f"❌ DB Connection Error: {err}")
        return None

def get_fresh_telegram_url(file_id):
    """Fetch a fresh URL for a file stored on Telegram using the file_id."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
        response = requests.get(url)

        if response.status_code == 200 and response.json().get("ok"):
            file_path = response.json()["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
            return file_url
        elif response.status_code == 404:
            logger.warning(f"⚠️  File not found on Telegram: file_id={file_id}")
            return None
        else:
            logger.error(f"❌ Telegram API error: {response.status_code}, {response.text}")
            return None  # File not found or error
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching URL: {e}")
        return None

def enhance_movie_data(movie):
    """Add video and poster URLs to the movie data."""
    try:
        # Get video URL.  Check if it is a URL or a file_id
        video_url = movie.get('video_link')
        if video_url:
            if video_url.startswith('http'):
                movie['video_url'] = video_url
            else:
                telegram_video_url = get_fresh_telegram_url(video_url)
                movie['video_url'] = telegram_video_url
        else:
            movie['video_url'] = None

        # Get poster URL
        if movie['poster_file_id']:
            movie['poster_url'] = get_fresh_telegram_url(movie['poster_file_id'])
        else:
            movie['poster_url'] = None

        return movie
    except Exception as e:
        logger.error(f"❌ Error enhancing movie data: {e}")
        return movie

@app.route("/movies", methods=["GET"])
def get_movies():
    """Fetch movies, optionally filtered by search and category."""
    try:
        search = request.args.get("search", "")
        category_id = request.args.get("category_id")

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT m.*, c.name AS category_name
        FROM movies m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE 1=1
        """
        params = []

        if search:
            query += " AND m.title LIKE %s"
            params.append(f"%{search}%")

        if category_id:
            query += " AND m.category_id = %s"
            params.append(category_id)

        query += " ORDER BY m.created_at DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Enhance each movie with video and poster URLs
        movies = [enhance_movie_data(movie) for movie in rows]

        return jsonify({
            "success": True,
            "count": len(movies),
            "data": movies,
            "generated_at": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Error fetching movies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/movie/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    """Fetch a specific movie by its ID."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT m.*, c.name AS category_name
        FROM movies m
        LEFT JOIN categories c ON m.category_id = c.id
        WHERE m.id = %s
        """
        cursor.execute(query, (movie_id,))
        movie = cursor.fetchone()

        cursor.close()
        conn.close()

        if movie:
            # Enhance the movie data with video and poster URLs
            movie = enhance_movie_data(movie)
            return jsonify({
                "success": True,
                "data": movie
            })
        else:
            return jsonify({"success": False, "error": "Movie not found"}), 404
    except Exception as e:
        logger.error(f"❌ Error fetching movie by ID: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/categories", methods=["GET"])
def get_categories():
    """Fetch all movie categories."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": categories})
    except Exception as e:
        logger.error(f"❌ Error fetching categories: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stream_video')
def stream_video():
    """
    Streams the video from the provided URL, acting as a proxy to handle CORS.
    """
    video_url = request.args.get('url')
    if not video_url:
        return "Video URL is required", 400
    logger.info(f"Attempting to stream video from: {video_url}")
    try:
        # Unquote the URL to handle any special characters
        video_url = unquote(video_url)
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            def generate():
                for chunk in response.iter_content(chunk_size=4096):
                    yield chunk
            resp = make_response(app.response_class(generate(), content_type=response.headers.get('Content-Type')))
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        else:
            logger.error(f"Error fetching video from source: {response.status_code} - {response.text}")
            return f"Error fetching video from source: {response.status_code}", response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during video stream proxy: {e}")
        return f"Error during video stream proxy: {e}", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)