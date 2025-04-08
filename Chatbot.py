from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import json

# ====== SETUP ======
TELEGRAM_TOKEN = "7700561986:AAECWAioYyrU3c7xxWrGKKyWqEi_k5e9310"  # From @BotFather
HF_API_KEY = "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"     # From Hugging Face
DEEPSEEK_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

# ====== DEEPSEEK AI QUERY ======
def ask_deepseek(user_input):
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        
        # Format the prompt to match instruction-tuned models
        prompt = f"### Instruction:\nYou are a helpful, friendly assistant. Answer conversationally.\n\n### Input:\n{user_input}\n\n### Response:"

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.7,
                "max_new_tokens": 200,
                "return_full_text": False
            }
        }

        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        data = response.json()

        # Some models return a list of generated texts
        if isinstance(data, list):
            return data[0].get('generated_text', '⚠️ No response from model.')
        elif isinstance(data, dict):
            if "generated_text" in data:
                return data["generated_text"]
            elif "error" in data:
                return f"❌ Error: {data['error']}"
            elif "generated_texts" in data:
                return data["generated_texts"][0]
            elif "choices" in data:  # For OpenAI-style outputs
                return data["choices"][0]["text"]
            else:
                return "⚠️ Unknown response structure."
        else:
            return "⚠️ Unexpected response format."

    except Exception as e:
        return f"❌ Exception occurred: {str(e)}"


# ====== TELEGRAM BOT ======
async def start(update: Update, context):
    await update.message.reply_text("👋 Hey, Akshay here. Whats up?")

async def reply_to_user(update: Update, context):
    try:
        await update.message.reply_text("⏳ Processing...")
        bot_response = ask_deepseek(update.message.text)
        await update.message.reply_text(bot_response)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\nPlease try again later.")

# ====== RUN THE BOT ======
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_user))
    app.run_polling()

if __name__ == "__main__":
    main()
