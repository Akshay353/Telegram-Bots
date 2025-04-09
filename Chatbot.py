from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import json
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
HF_API_KEY = os.environ.get("HF_API_KEY")     # From Hugging Face
DEEPSEEK_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

# ====== DEEPSEEK AI QUERY ======
def ask_deepseek(user_id, user_input):
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        
        # Initialize memory if new user
        if user_id not in user_memory:
            user_memory[user_id] = []

        # Add new user input to memory
        user_memory[user_id].append({"role": "user", "content": user_input})

        # Construct prompt using memory
        chat_prompt = ""
        for msg in user_memory[user_id]:
            if msg["role"] == "user":
                chat_prompt += f"### Input:\n{msg['content']}\n\n"
            else:
                chat_prompt += f"### Response:\n{msg['content']}\n\n"

        chat_prompt += "### Response:"

        payload = {
            "inputs": chat_prompt,
            "parameters": {
                "temperature": 0.7,
                "max_new_tokens": 200,
                "return_full_text": False
            }
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        data = response.json()

        print("🌐 STATUS CODE:", response.status_code)
        print("⚠️ RAW RESPONSE:", data)

        # Get the bot's response
        if isinstance(data, list):
            bot_reply = data[0].get('generated_text', '⚠️ No response from model.')
        elif "generated_text" in data:
            bot_reply = data["generated_text"]
        else:
            bot_reply = f"⚠️ Unexpected format. Raw data: {str(data)}"

        # Save bot reply to memory
        user_memory[user_id].append({"role": "assistant", "content": bot_reply})
        return bot_reply

    except Exception as e:
        return f"❌ Exception: {str(e)}"


# ====== TELEGRAM BOT ======
async def start(update: Update, context):
    await update.message.reply_text("👋 Hey, Akshay here. Whats up?")

async def reply_to_user(update: Update, context):
    try:
        user_id = update.message.from_user.id
        user_input = update.message.text
        await update.message.reply_text("⏳ Thinking...")

        bot_response = ask_deepseek(user_id, user_input)
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
