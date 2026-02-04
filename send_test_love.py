import os
import asyncio
import logging
import google.generativeai as genai
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)

async def send_test_message():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    gf_id = os.getenv('GIRLFRIEND_CHAT_ID')
    api_key = os.getenv('GOOGLE_API_KEY')

    if not token or not gf_id or not api_key:
        print("Error: Missing credentials in .env")
        return

    # Configure Gemini
    genai.configure(api_key=api_key)
    
    candidate_models = [
        'gemini-2.0-flash-lite',
        'gemini-flash-latest',
        'gemini-1.5-flash',
        'gemini-2.0-flash'
    ]

    print("Generiere Nachricht...")
    message_text = None
    
    for model_name in candidate_models:
        print(f"Versuche Modell: {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            prompt = (
                "Schreibe eine kurze, liebevolle Guten-Morgen-Nachricht an meine Freundin. "
                "WICHTIG: Schreibe aus MEINER Perspektive (Ich-Form). "
                "Erwähne NIEMALS, dass du eine KI, ein Bot oder ein Programm bist. "
                "Es darf nicht wie ein Test klingen. "
                "Der Ton soll romantisch, persönlich und warmherzig sein. "
                "Wünsche ihr einen wunderschönen Tag und sag ihr, dass ich an sie denke. "
                "Nutze ein paar Emojis, aber nicht zu viele."
            )
            response = model.generate_content(prompt)
            message_text = response.text
            print(f"Erfolg mit {model_name}!")
            break
        except Exception as e:
            print(f"Fehler mit {model_name}: {e}")

    if not message_text:
        message_text = "Test-Nachricht: Ich liebe dich! (Alle AI-Modelle sind gerade ausgelastet)"

    bot = Bot(token=token)
    print(f"Sende Nachricht an {gf_id}...")
    await bot.send_message(chat_id=gf_id, text=message_text)
    print("Nachricht gesendet!")

if __name__ == "__main__":
    asyncio.run(send_test_message())
