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
    t = threading.Thread(target=run)
    t.start()


# ====== SETUP ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")  # From @BotFather
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # From Google Cloud AI Platform or Google AI Studio

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') # Using a faster, less creative model

# ====== GEMINI AI QUERY ======
async def ask_gemini(user_id, user_input):
    try:
        # Initialize memory if new user
        if user_id not in user_memory:
            user_memory[user_id] = []
            # Add a system message to guide the bot's behavior for new users
            user_memory[user_id].append({"role": "model", "parts": ["You are a friendly, helpful, and concise assistant. You should be creative and chill at times but be accurate and don't make things up."]})

        # Add new user input to memory
        user_memory[user_id].append({"role": "user", "parts": [user_input]})

        # Construct conversation history
        conversation = model.start_chat(history=user_memory.get(user_id, []))

        # Send message with temperature set low for less creativity
        response = await conversation.send_message_async(
            user_input,
            generation_config={"temperature": 0.7}  # Lower temperature for less creativity
        )
        bot_reply = response.text

        # Save bot reply to memory
        user_memory[user_id].append({"role": "model", "parts": [bot_reply]})
        return bot_reply

    except Exception as e:
        return f"❌ Exception: {str(e)}"


# ====== TELEGRAM BOT ======
async def start(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(f"👋 Hi, Akshay here, what's up?")

async def reply_to_user(update: Update, context):
    try:
        user_id = update.message.from_user.id
        user_input = update.message.text
        await update.message.reply_text("⏳ Thinking...")

        bot_response = await ask_gemini(user_id, user_input)
        await update.message.reply_text(bot_response)

    except Exception as e:
        await update.message.reply_text(f"❌ Oh no! Something went wrong: {str(e)}")

async def greet_command(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(f"Hey {user.first_name}! Nice to see you again.")

async def help_command(update: Update, context):
    help_text = (
        "I'm a friendly bot powered by Google AI. Just send me a message, and I'll do my best to help!\n\n"
        "Here are a few things you can try:\n"
        "- Ask me a question.\n"
        "- Tell me something interesting.\n"
        "- Just say hi!\n\n"
        "I'm still learning, so please be patient with me."
    )
    await update.message.reply_text(help_text)

# ====== RUN THE BOT ======
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("greet", greet_command))
    app.add_handler(CommandHandler("help", help_command))

    # Add message handler for all other text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_user))

    app.run_polling()

keep_alive()
main()

if __name__ == "__main__":
    main()
