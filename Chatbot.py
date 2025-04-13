from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import google.generativeai as genai
import os
from flask import Flask
import threading

user_memory = {}

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()


# ====== SETUP ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # From @BotFather
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # From Google Cloud AI Platform or Google AI Studio

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro') # Or 'gemini-pro-vision' for multimodal


# ====== GEMINI AI QUERY ======
async def ask_gemini(user_id, user_input):
    try:
        # Initialize memory if new user
        if user_id not in user_memory:
            user_memory[user_id] = []

        # Add new user input to memory
        user_memory[user_id].append({"role": "user", "parts": [user_input]})

        # Construct conversation history
        conversation = model.start_chat(history=user_memory.get(user_id, []))
        response = await conversation.send_message_async(user_input)
        bot_reply = response.text

        # Save bot reply to memory
        user_memory[user_id].append({"role": "model", "parts": [bot_reply]})
        return bot_reply

    except Exception as e:
        return f"❌ Exception: {str(e)}"


# ====== TELEGRAM BOT ======
async def start(update: Update, context):
    await update.message.reply_text("👋 Hey, I'm now powered by Gemini! What's up?")

async def reply_to_user(update: Update, context):
    try:
        user_id = update.message.from_user.id
        user_input = update.message.text
        await update.message.reply_text("⏳ Thinking with Gemini...")

        bot_response = await ask_gemini(user_id, user_input)
        await update.message.reply_text(bot_response)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ====== RUN THE BOT ======
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_user))
    app.run_polling()

keep_alive()
main()

if __name__ == "__main__":
    main()
