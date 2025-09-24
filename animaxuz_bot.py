# file: animaxuz_bot.py
import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

load_dotenv()
TELEGRAM_TOKEN = os.getenv("animaxuz_bot")
TMDB_KEY = os.getenv("8117563003:AAGUQV5d5S6QHqrJul6hTIIo96AbWQ-0Rj8")
TMDB_BASE = "https://api.themoviedb.org/3"

def tmdb_search(query):
    params = {"api_key": TMDB_KEY, "query": query, "language": "en-US", "include_adult": False}
    r = requests.get(f"{TMDB_BASE}/search/movie", params=params)
    r.raise_for_status()
    return r.json().get("results", [])

def tmdb_movie_details(movie_id):
    params = {"api_key": TMDB_KEY, "language": "en-US", "append_to_response": "videos,credits"}
    r = requests.get(f"{TMDB_BASE}/movie/{movie_id}", params=params)
    r.raise_for_status()
    return r.json()

def poster_url(path, size="w500"):
    if not path:
        return None
    return f"https://image.tmdb.org/t/p/{size}{path}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! /search <film nomi> bilan qidirishingiz mumkin.")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Iltimos film nomini yozing: /search Interstellar")
        return
    query = " ".join(context.args)
    results = tmdb_search(query)[:6]  # bir necha natija
    if not results:
        await update.message.reply_text("Topilmadi.")
        return
    buttons = []
    for r in results:
        title = f"{r.get('title')} ({r.get('release_date','')[:4]})" if r.get('release_date') else r.get('title')
        buttons.append([InlineKeyboardButton(title, callback_data=f"movie_{r['id']}")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(f"Natijalar uchun: {query}", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("movie_"):
        movie_id = data.split("_",1)[1]
        details = tmdb_movie_details(movie_id)
        title = details.get("title")
        overview = details.get("overview") or "Ta'rif yo'q."
        year = details.get("release_date","")[:4]
        poster = poster_url(details.get("poster_path"))
        # top trailer (YouTube)
        videos = details.get("videos", {}).get("results", [])
        trailer_url = None
        for v in videos:
            if v.get("site") == "YouTube" and v.get("type") in ("Trailer","Teaser"):
                trailer_url = f"https://www.youtube.com/watch?v={v.get('key')}"
                break
        text = f"*{title}* ({year})\n\n{overview}\n\nRating: {details.get('vote_average')} / 10"
        buttons = []
        if trailer_url:
            buttons.append([InlineKeyboardButton("Trailerni ko'rish", url=trailer_url)])
        # ehtimol rasmiy saytlarga yoki platforma API havolasiga qo'shing (agar ma'lum bo'lsa)
        if poster:
            await query.message.reply_photo(poster, caption=text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)
        else:
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
