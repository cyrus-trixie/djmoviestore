import os
import mysql.connector
import logging
import requests
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message
from aiogram.enums import ContentType
from aiogram import F
import asyncio
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)

# Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN")  # Get token from environment variable
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Function to establish MySQL connection using environment variables
def get_db_connection():
    """Establish and return a MySQL database connection using environment variables."""
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")

    if not all([db_host, db_port, db_user, db_password, db_name]):
        logging.error("❌ One or more database environment variables are not set for bot.")
        return None

    try:
        connection = mysql.connector.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name,
            autocommit=True,
            charset='utf8mb4'  # Recommended charset
        )
        return connection
    except mysql.connector.Error as err:
        logging.error(f"❌ Database connection failed for bot: {err}")
        return None

# Get database connection (call the function)
db_connection = get_db_connection()
if db_connection:
    cursor = db_connection.cursor()
    logging.info("✅ Bot connected to MySQL database successfully.")
else:
    logging.error("❌ Bot failed to connect to MySQL database.")
    exit()

# States for movie upload process
class MovieUpload(StatesGroup):
    waiting_for_video_link = State()
    waiting_for_title = State()
    waiting_for_image = State()
    waiting_for_category = State()
    waiting_for_dj = State() # New state for DJ selection

# Function to fetch all DJs from the database
async def get_all_djs():
    try:
        cursor.execute("SELECT id, name FROM djs ORDER BY name")
        djs = cursor.fetchall()
        return djs
    except Exception as e:
        logging.error(f"❌ Error fetching DJs from database: {e}")
        return []

# Function to save movie data in MySQL (updated with category, video link, and DJ ID)
def save_movie(title, video_link, poster_file_id, chat_id, category_id=None, dj_id=None):
    try:
        check_sql = "SELECT id FROM movies WHERE video_link = %s"
        cursor.execute(check_sql, (video_link,))
        result = cursor.fetchone()

        if result:
            update_sql = """
            UPDATE movies
            SET title = %s, video_link = %s, poster_file_id = %s, category_id = %s, dj_id = %s
            WHERE video_link = %s
            """
            cursor.execute(update_sql, (title, video_link, poster_file_id, category_id, dj_id, video_link))
        else:
            sql = """
            INSERT INTO movies (title, video_link, poster_file_id, user_id, category_id, dj_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (title, video_link, poster_file_id, chat_id, category_id, dj_id)
            cursor.execute(sql, values)

        db_connection.commit()
        logging.info(f"✅ Bot saved movie '{title}' with category {category_id} and DJ {dj_id}")
        return True
    except Exception as e:
        logging.error(f"❌ Error saving movie from bot: {e}")
        return False

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Welcome to Movie Bot! 🎬\n\n"
        "To add a movie:\n"
        "1. Send /addmovie\n"
        "2. Upload the video link (cloud storage URL)\n"
        "3. Upload the poster image\n"
        "4. Select a category\n"
        "5. Select a DJ"
    )

@router.message(Command("addmovie"))
async def cmd_add_movie(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Please send me the movie's video link (from cloud storage)."
    )
    await state.set_state(MovieUpload.waiting_for_video_link) # Set state to wait for video link

@router.message(MovieUpload.waiting_for_video_link, F.content_type == ContentType.TEXT)
async def receive_video_link(message: Message, state: FSMContext):
    if message.chat.type == "private":
        video_link = message.text.strip()

        # Basic validation for a URL (you might want to add more robust validation)
        if video_link.startswith("http"):
            await state.update_data({'video_link': video_link})

            await message.reply(
                "🎬 Video link received! Now please provide the movie title.",
                reply_markup=types.ReplyKeyboardRemove() # Remove any previous keyboard
            )

            # Set state to wait for the movie title
            await state.set_state(MovieUpload.waiting_for_title) # Set state to wait for title
        else:
            await message.reply("❌ Please provide a valid video link (starting with http).")
    else:
        await message.reply("❌ Please provide a valid video link.")

@router.message(MovieUpload.waiting_for_title, F.content_type == ContentType.TEXT)
async def receive_movie_title(message: Message, state: FSMContext):
    title = message.text.strip()

    if title: # If title is provided
        await state.update_data({'title': title})

        # Ask for the poster image
        await message.reply("🖼️ Now, please send the movie's poster image.")
        await state.set_state(MovieUpload.waiting_for_image) # Change state to wait for poster
    else:
        await message.reply("❌ Movie title is required. Please provide a valid title.")

@router.message(F.content_type == ContentType.PHOTO)
async def receive_image(message: Message, state: FSMContext):
    if message.chat.type == "private":
        poster_file_id = message.photo[-1].file_id # Save file_id instead of URL

        await state.update_data({'poster_file_id': poster_file_id})
        data = await state.get_data()

        if data.get('video_link'):
            # Fetch available categories from the database
            cursor.execute("SELECT id, name FROM categories")
            categories = cursor.fetchall()

            if categories:
                # Create reply keyboard with categories
                keyboard_categories = types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text=category[1])] for category in categories],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                await message.reply(
                    "🖼️ Poster received! Now please select a category from the keyboard.",
                    reply_markup=keyboard_categories
                )

                await state.set_state(MovieUpload.waiting_for_category) # Move to category selection state
            else:
                await message.reply("❌ No categories found in the database. Please add categories first.")
        else:
            await message.reply("❌ Please send a video link first using /addmovie command.")
    else:
        await message.reply("❌ Failed to process the image.")

@router.message(MovieUpload.waiting_for_category, F.content_type == ContentType.TEXT)
async def receive_category(message: Message, state: FSMContext):
    category_name = message.text
    cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
    category = cursor.fetchone()

    if category:
        category_id = category[0]
        await state.update_data({'category_id': category_id})

        # Fetch available DJs from the database
        djs = await get_all_djs()
        if djs:
            # Create reply keyboard with DJs
            keyboard_djs = types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text=dj[1])] for dj in djs],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            await message.reply(
                "🏷️ Category selected! Now please select the DJ for this movie.",
                reply_markup=keyboard_djs
            )
            await state.set_state(MovieUpload.waiting_for_dj) # Move to DJ selection state
        else:
            await message.reply("⚠️ No DJs found in the database. The movie will be saved without a DJ.", reply_markup=types.ReplyKeyboardRemove())
            data = await state.get_data()
            if save_movie(
                title=data['title'],
                video_link=data['video_link'],
                poster_file_id=data['poster_file_id'],
                chat_id=message.from_user.id,
                category_id=category_id,
                dj_id=None
            ):
                await message.reply(f"✅ Movie '{data['title']}' saved successfully in {category_name}!", reply_markup=types.ReplyKeyboardRemove())
            else:
                await message.reply("❌ Error saving movie to database.")
            await state.clear()
    else:
        await message.reply("❌ Invalid category. Please select from the keyboard.")

@router.message(MovieUpload.waiting_for_dj, F.content_type == ContentType.TEXT)
async def receive_dj(message: Message, state: FSMContext):
    dj_name = message.text
    cursor.execute("SELECT id FROM djs WHERE name = %s", (dj_name,))
    dj = cursor.fetchone()

    data = await state.get_data()
    category_id = data.get('category_id')

    if dj:
        dj_id = dj[0]
        # Fetch category name *before* saving, and handle the case where the category is not found.
        cursor.execute("SELECT name FROM categories WHERE id = %s", (category_id,))
        category_result = cursor.fetchone()
        category_name = category_result[0] if category_result else "Unknown Category" #added

        if save_movie(
            title=data['title'],
            video_link=data['video_link'],
            poster_file_id=data['poster_file_id'],
            chat_id=message.from_user.id,
            category_id=category_id,
            dj_id=dj_id
        ):
            await message.reply(
                f"✅ Movie '{data['title']}' saved successfully in "
                f"(category: {category_name}, " #used variable
                f"DJ: {dj_name})!",
                reply_markup=types.ReplyKeyboardRemove() # Remove the keyboard after completion
            )
        else:
            await message.reply("❌ Error saving movie to database.")
        await state.clear() # Clear state after movie is saved
    else:
        await message.reply("❌ Invalid DJ name. Please select from the keyboard.")

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Operation canceled. You can start again with /addmovie.",
        reply_markup=types.ReplyKeyboardRemove()
    )

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
