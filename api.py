import os
from flask import Flask, jsonify, request, send_file, make_response, send_from_directory
from flask_cors import CORS
import MySQLdb  # Changed import
import logging
import requests
from datetime import datetime
from urllib.parse import unquote
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


# Function to establish MySQL connection using environment variables.
def get_db_connection():
    """Establish and return a MySQL database connection using environment variables."""
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")

    if not all([db_host, db_port, db_user, db_password, db_name]):
        logger.error("❌ One or more database environment variables are not set.")
        return None

    try:
        connection = MySQLdb.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            passwd=db_password,
            db=db_name,
            autocommit=True,
            charset='utf8mb4',  # Recommended charset
        )
        return connection
    except MySQLdb.Error as err:
        logger.error(f"❌ DB Connection Error: {err}")
        return None


# Function to fetch a fresh URL for a file stored on Telegram using the file_id.
def get_fresh_telegram_url(file_id):
    """Fetch a fresh URL for a file stored on Telegram using the file_id."""
    if not file_id:
        logger.warning("⚠️  file_id is empty")
        return None

    try:
        telegram_token = os.environ.get("TELEGRAM_TOKEN")
        if not telegram_token:
            logger.error("❌ TELEGRAM_TOKEN environment variable is not set.")
            return None
        url = f"https://api.telegram.org/bot{telegram_token}/getFile?file_id={file_id}"
        response = requests.get(url)

        if response.status_code == 200 and response.json().get("ok"):
            file_path = response.json()["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{telegram_token}/{file_path}"
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
    if not movie:
        return None

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


@app.route("/", methods=["GET"])
def index():
    """Handles requests to the root URL."""
    return jsonify({"message": "Welcome to the Movie API"})  # Or any other appropriate response


@app.route('/favicon.ico')
def favicon():
    """Serves the favicon.ico file."""
    return send_from_directory(app.root_path, 'static/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


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

        return jsonify(
            {
                "success": True,
                "count": len(movies),
                "data": movies,
                "generated_at": datetime.now().isoformat(),
            }
        )
    except MySQLdb.Error as db_err:  # Catch DB errors specifically
        logger.error(f"❌ Database error fetching movies: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
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
            return jsonify({"success": True, "data": movie})
        else:
            return jsonify({"success": False, "error": "Movie not found"}), 404
    except MySQLdb.Error as db_err:  # Catch DB errors.
        logger.error(f"❌ Database error fetching movie: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
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
    except MySQLdb.Error as db_err:  # Catch the specific exception
        logger.error(f"❌ Database error fetching categories: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
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
        response = requests.get(video_url, stream=True, timeout=10)  # Add timeout
        if response.status_code == 200:

            def generate():
                for chunk in response.iter_content(chunk_size=4096):
                    yield chunk

            resp = make_response(app.response_class(generate(),
                                                   content_type=response.headers.get('Content-Type')))
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year caching
            return resp
        else:
            logger.error(
                f"Error fetching video from source: {response.status_code} - {response.text}")
            return f"Error fetching video from source: {response.status_code}", response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during video stream proxy: {e}")
        return f"Error during video stream proxy: {e}", 500
    except Exception as e:
        logger.error(f"Unexpected error in stream_video: {e}")
        return "Internal server error", 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
