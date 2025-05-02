from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Function to ask ChatGPT
async def ask_gpt(message_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI travel assistant. "
                        "Ask the user questions about their trip preferences, "
                        "then suggest a vacation destination and generate a full plan "
                        "(including flights, hotel suggestions, activities, and budget)."
                    ),
                },
                {"role": "user", "content": message_text},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GPT Error: {str(e)}"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your Trip Planner Bot.\nTell me what kind of vacation you'd like!"
    )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    reply = await ask_gpt(user_input)
    await update.message.reply_text(reply)

# Bot setup
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Trip Planner Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
