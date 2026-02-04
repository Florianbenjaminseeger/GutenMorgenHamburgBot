import os
import re
import logging
import datetime
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from keep_alive import start_keep_alive  # Import keep_alive

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from calendar_utils import get_todays_events

# Load environment variables
load_dotenv()

# Start keep-alive server for Render
start_keep_alive()

# Configure Gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found in .env")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Store chat sessions in memory: chat_id -> chat_session
chat_sessions = {}

def get_weather_hamburg():
    """Fetches simple weather data for Hamburg."""
    try:
        # Hamburg coordinates
        url = "https://api.open-meteo.com/v1/forecast?latitude=53.55&longitude=9.99&current=temperature_2m,weather_code&hourly=temperature_2m&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Europe%2FBerlin&forecast_days=1"
        response = requests.get(url)
        data = response.json()
        
        current_temp = data['current']['temperature_2m']
        max_temp = data['daily']['temperature_2m_max'][0]
        min_temp = data['daily']['temperature_2m_min'][0]
        
        return (
            f"🌦 **Wetter in Hamburg**\n"
            f"Aktuell: {current_temp}°C\n"
            f"Tageswerte: {min_temp}°C bis {max_temp}°C"
        )
    except Exception as e:
        logging.error(f"Weather error: {e}")
        return "⚠️ Wetter konnte nicht geladen werden."

def get_daily_briefing():
    """Combines weather and calendar events for a daily briefing."""
    weather = get_weather_hamburg()
    
    email = os.getenv('ICLOUD_EMAIL')
    password = os.getenv('ICLOUD_PASSWORD')
    
    if email and password:
        calendar_info = get_todays_events(email, password)
    else:
        calendar_info = "⚠️ iCloud Zugangsdaten fehlen in der .env Datei."
        
    return f"{weather}\n\n{calendar_info}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message and schedules the daily job."""
    chat_id = update.effective_chat.id
    
    # Reset chat session on start
    if chat_id in chat_sessions:
        del chat_sessions[chat_id]

    # Schedule the daily morning message
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    context.job_queue.run_daily(
        send_morning_message, 
        time=datetime.time(hour=7, minute=00), 
        chat_id=chat_id, 
        name=str(chat_id),
        data=chat_id
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"👋 Hallo! Ich bin dein AI-Assistent.\n"
             f"Dein Briefing kommt täglich um 07:00 Uhr.\n"
             f"Du kannst mit mir ganz normal schreiben, ich antworte dir mit der Power von Google Gemini."
    )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the weather immediately."""
    report = get_weather_hamburg()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=report)

async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the full daily briefing immediately."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Einen Moment, ich lade deine Daten..."
    )
    report = get_daily_briefing()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=report)

async def send_morning_message(context: ContextTypes.DEFAULT_TYPE):
    """Callback for the daily job."""
    chat_id = context.job.data
    report = get_daily_briefing()
    await context.bot.send_message(chat_id=chat_id, text=report)

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user messages by sending them to Gemini."""
    chat_id = update.effective_chat.id
    user_text = update.message.text
    
    # Notify user that we are thinking (optional, but good UX)
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    
    try:
        # Check if we have an active session
        if chat_id not in chat_sessions:
            model = genai.GenerativeModel('gemini-flash-latest')
            chat_sessions[chat_id] = model.start_chat(history=[])
        
        chat = chat_sessions[chat_id]
        response = chat.send_message(user_text)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=response.text,
            parse_mode="Markdown" # Gemini produces Markdown
        )
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Entschuldigung, ich habe gerade Schwierigkeiten zu antworten."
        )

async def get_ai_love_message():
    """Generates a sweet, unique good morning message using Gemini."""
    try:
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = (
            "Schreibe eine kurze, liebevolle Guten-Morgen-Nachricht an meine Freundin. "
            "WICHTIG: Schreibe aus MEINER Perspektive (Ich-Form). "
            "Erwähne NIEMALS, dass du eine KI, ein Bot oder ein Programm bist. "
            "Es darf nicht wie ein Test klingen. "
            "Der Ton soll romantisch, persönlich und warmherzig sein. "
            "Wünsche ihr einen wunderschönen Tag und sag ihr, dass ich an sie denke. "
            "Nutze ein paar Emojis, aber nicht zu viele. "
            "Antworte als reinen Text. Keine Formatierung."
        )
        response = model.generate_content(prompt)
        
        # Cleanup: Remove any HTML-like tags (including blockquote) and quotes
        text = response.text
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        # Remove surrounding quotes if present
        if clean_text.startswith('"') and clean_text.endswith('"'):
            clean_text = clean_text[1:-1]
            
        return clean_text
    except Exception as e:
        logging.error(f"Love message error: {e}")
        return "Guten Morgen mein Schatz! ❤️ Ich liebe dich über alles!"

async def send_girlfriend_message(context: ContextTypes.DEFAULT_TYPE):
    """Callback to send the daily love message."""
    chat_id = context.job.data
    message = await get_ai_love_message()
    await context.bot.send_message(chat_id=chat_id, text=message)

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a love message immediately."""
    # Only allowed for girlfriend or owner (optional security, but good practice)
    # For now, open to use.
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    message = await get_ai_love_message()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns the chat ID."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Deine Chat-ID ist: `{update.effective_chat.id}`",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file.")
        exit(1)

    application = ApplicationBuilder().token(token).build()
    job_queue = application.job_queue

    # Schedule Girlfriend Message if ID is present
    gf_id = os.getenv('GIRLFRIEND_CHAT_ID')
    if gf_id:
        print(f"Scheduling love messages for ID: {gf_id}")
        # Remove existing jobs for her to avoid duplicates on restart
        for job in job_queue.get_jobs_by_name("girlfriend_love"):
            job.schedule_removal()
            
        job_queue.run_daily(
            send_girlfriend_message,
            time=datetime.time(hour=7, minute=0), # 7:00 AM
            chat_id=int(gf_id),
            name="girlfriend_love",
            data=int(gf_id)
        )

    start_handler = CommandHandler('start', start)
    weather_handler = CommandHandler('weather', weather_command)
    briefing_handler = CommandHandler('briefing', briefing_command)
    id_handler = CommandHandler('id', id_command)
    love_handler = CommandHandler('love', love_command)
    
    # Replaces Echo with AI
    ai_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_ai_message)
    
    application.add_handler(start_handler)
    application.add_handler(weather_handler)
    application.add_handler(briefing_handler)
    application.add_handler(id_handler)
    application.add_handler(love_handler)
    application.add_handler(ai_handler)
    
    print("Bot is successfully running...")
    application.run_polling()
