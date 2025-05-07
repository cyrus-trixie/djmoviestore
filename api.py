import os
import logging
from datetime import datetime
from urllib.parse import unquote

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import pymysql
from pymysql.cursors import DictCursor
import requests
from dotenv import load_dotenv

# Monkey patch BEFORE doing anything else
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder="build", static_url_path="/")
CORS(app)

# Database connection
def get_db_connection():
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")

    if not all([db_host, db_port, db_user, db_password, db_name]):
        logger.error("❌ One or more database environment variables are not set.")
        return None

    try:
        connection = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name,
            autocommit=True,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        return connection
    except pymysql.MySQLError as err:
        logger.error(f"❌ DB Connection Error: {err}")
        return None

# Telegram file URL retrieval
def get_fresh_telegram_url(file_id):
    if not file_id:
        logger.warning("⚠️ file_id is empty")
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
            return f"https://api.telegram.org/file/bot{telegram_token}/{file_path}"
        elif response.status_code == 404:
            logger.warning(f"⚠️ File not found on Telegram: file_id={file_id}")
            return None
        else:
            logger.error(f"❌ Telegram API error: {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching URL: {e}")
        return None

# Enhance movie data with media URLs
def enhance_movie_data(movie):
    if not movie:
        return None
    try:
        video_url = movie.get('video_link')
        movie['video_url'] = (
            video_url if video_url and video_url.startswith('http') else get_fresh_telegram_url(video_url)
        )
        movie['poster_url'] = (
            get_fresh_telegram_url(movie.get('poster_file_id')) if movie.get('poster_file_id') else None
        )
        return movie
    except Exception as e:
        logger.error(f"❌ Error enhancing movie data: {e}")
        return movie

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the Movie API"})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'static/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/movies", methods=["GET"])
def get_movies():
    try:
        search = request.args.get("search", "")
        category_id = request.args.get("category_id")
        dj_id = request.args.get("dj_id")

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        with conn.cursor() as cursor:
            query = """
            SELECT m.*, c.name AS category_name, d.name AS dj_name, d.id AS dj_id
            FROM movies m
            LEFT JOIN categories c ON m.category_id = c.id
            LEFT JOIN djs d ON m.dj_id = d.id
            WHERE 1=1
            """
            params = []
            if search:
                query += " AND m.title LIKE %s"
                params.append(f"%{search}%")
            if category_id:
                query += " AND m.category_id = %s"
                params.append(category_id)
            if dj_id:
                query += " AND m.dj_id = %s"
                params.append(dj_id)

            query += " ORDER BY m.created_at DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

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
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.*, c.name AS category_name, d.name AS dj_name, d.id AS dj_id
                FROM movies m
                LEFT JOIN categories c ON m.category_id = c.id
                LEFT JOIN djs d ON m.dj_id = d.id
                WHERE m.id = %s
            """, (movie_id,))
            movie = cursor.fetchone()

        if movie:
            return jsonify({"success": True, "data": enhance_movie_data(movie)})
        else:
            return jsonify({"success": False, "error": "Movie not found"}), 404
    except Exception as e:
        logger.error(f"❌ Error fetching movie by ID: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/categories", methods=["GET"])
def get_categories():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM categories ORDER BY name")
            categories = cursor.fetchall()

        return jsonify({"success": True, "data": categories})
    except Exception as e:
        logger.error(f"❌ Error fetching categories: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/djs", methods=["GET"])
def get_djs():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM djs ORDER BY name")
            djs = cursor.fetchall()

        return jsonify({"success": True, "data": djs})
    except Exception as e:
        logger.error(f"❌ Error fetching DJs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/stream_video')
def stream_video():
    video_url = request.args.get('url')
    if not video_url:
        return "Video URL is required", 400

    logger.info(f"Attempting to stream video from: {video_url}")
    try:
        video_url = unquote(video_url)
        response = requests.get(video_url, stream=True, timeout=10)

        if response.status_code == 200:
            def generate():
                for chunk in response.iter_content(chunk_size=4096):
                    yield chunk

            resp = make_response(app.response_class(generate(), content_type=response.headers.get('Content-Type')))
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Cache-Control'] = 'public, max-age=31536000'
            return resp
        else:
            logger.error(f"Error fetching video from source: {response.status_code} - {response.text}")
            return f"Failed to fetch video. Status: {response.status_code}", 500
    except Exception as e:
        logger.error(f"❌ Error streaming video: {e}")
        return f"Internal server error: {e}", 500
