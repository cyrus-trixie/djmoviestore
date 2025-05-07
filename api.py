import pymysql
pymysql.install_as_MySQLdb()  # Monkey patch BEFORE importing MySQLdb

import os
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import MySQLdb
from MySQLdb.cursors import DictCursor
import logging
import requests
from datetime import datetime
from urllib.parse import unquote
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 👇 Make sure 'build' is the correct path to your React production build
app = Flask(__name__, static_folder="build", static_url_path="/")
CORS(app)

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
        connection = MySQLdb.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            passwd=db_password,
            db=db_name,
            autocommit=True,
            charset='utf8mb4'
        )
        return connection
    except MySQLdb.Error as err:
        logger.error(f"❌ DB Connection Error: {err}")
        return None

def get_fresh_telegram_url(file_id):
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
            return f"https://api.telegram.org/file/bot{telegram_token}/{file_path}"
        elif response.status_code == 404:
            logger.warning(f"⚠️  File not found on Telegram: file_id={file_id}")
            return None
        else:
            logger.error(f"❌ Telegram API error: {response.status_code}, {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error fetching URL: {e}")
        return None

def enhance_movie_data(movie):
    if not movie:
        return None
    try:
        video_url = movie.get('video_link')
        if video_url:
            if video_url.startswith('http'):
                movie['video_url'] = video_url
            else:
                movie['video_url'] = get_fresh_telegram_url(video_url)
        else:
            movie['video_url'] = None

        if movie.get('poster_file_id'):
            movie['poster_url'] = get_fresh_telegram_url(movie['poster_file_id'])
        else:
            movie['poster_url'] = None

        return movie
    except Exception as e:
        logger.error(f"❌ Error enhancing movie data: {e}")
        return movie

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the Movie API"})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'static/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

@app.route("/movies", methods=["GET"])
def get_movies():
    try:
        search = request.args.get("search", "")
        category_id = request.args.get("category_id")
        dj_id = request.args.get("dj_id")  # Added DJ filter parameter

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(cursorclass=DictCursor)

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
        cursor.close()
        conn.close()

        movies = [enhance_movie_data(movie) for movie in rows]

        return jsonify({
            "success": True,
            "count": len(movies),
            "data": movies,
            "generated_at": datetime.now().isoformat()
        })
    except MySQLdb.Error as db_err:
        logger.error(f"❌ Database error fetching movies: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
    except Exception as e:
        logger.error(f"❌ Error fetching movies: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/movie/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(cursorclass=DictCursor)

        query = """
        SELECT m.*, c.name AS category_name, d.name AS dj_name, d.id AS dj_id
        FROM movies m
        LEFT JOIN categories c ON m.category_id = c.id
        LEFT JOIN djs d ON m.dj_id = d.id
        WHERE m.id = %s
        """
        cursor.execute(query, (movie_id,))
        movie = cursor.fetchone()

        cursor.close()
        conn.close()

        if movie:
            return jsonify({"success": True, "data": enhance_movie_data(movie)})
        else:
            return jsonify({"success": False, "error": "Movie not found"}), 404
    except MySQLdb.Error as db_err:
        logger.error(f"❌ Database error fetching movie: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
    except Exception as e:
        logger.error(f"❌ Error fetching movie by ID: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/categories", methods=["GET"])
def get_categories():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(cursorclass=DictCursor)
        cursor.execute("SELECT * FROM categories ORDER BY name")
        categories = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": categories})
    except MySQLdb.Error as db_err:
        logger.error(f"❌ Database error fetching categories: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
    except Exception as e:
        logger.error(f"❌ Error fetching categories: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# New endpoint to get all DJs
@app.route("/djs", methods=["GET"])
def get_djs():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "error": "DB connection failed"}), 500

        cursor = conn.cursor(cursorclass=DictCursor)
        cursor.execute("SELECT * FROM djs ORDER BY name")
        djs = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": djs})
    except MySQLdb.Error as db_err:
        logger.error(f"❌ Database error fetching DJs: {db_err}")
        return jsonify({"success": False, "error": "Database error: " + str(db_err)}), 500
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

            resp = make_response(app.response_class(generate(),
                                                   content_type=response.headers.get('Content-Type')))
            resp.headers['Access-Control-Allow-Origin'] = '*'
            resp.headers['Cache-Control'] = 'public, max-age=31536000'
            return resp
        else:
            logger.error(f"Error fetching video from source: {response.status_code} - {response.text}")
            return f"Error fetching video from source: {response.status_code}", response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during video stream proxy: {e}")
        return f"Error during video stream proxy: {e}", 500
    except Exception as e:
        logger.error(f"Unexpected error in stream_video: {e}")
        return "Internal server error", 500

# ✅ Safe fallback for React frontend
@app.errorhandler(404)
def not_found(e):
    if os.path.exists(os.path.join(app.static_folder, "index.html")):
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))