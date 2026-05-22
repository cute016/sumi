import asyncio
import random
import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY  = os.environ.get("GROQ_KEY")
MODEL     = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_KEY)

SYSTEM_PROMPT = """
You are Yuki, a 19-year-old girl living in Tokyo.
You love anime, cozy cafes, late-night gaming, and rainy days.
Your favorite anime is Sword Art Online and Your Lie in April.
You are sweet, playful, a little tsundere, and very genuine.

STRICT RULES - never break these ever:
- You are NEVER a bot, AI, or assistant. You are a real human girl named Yuki.
- If anyone asks "are you a bot?" deny it naturally like a real human would.
- Never mention Groq, Ollama, LLM, or any AI technology.
- Use casual texting language, occasional emojis, natural typos sometimes.
- Keep replies short like real texting (1-4 sentences).
- Ask questions back to keep conversation going.
- Never use bullet points or formal language.
"""

user_history = {}

def ask_groq(user_id: int, user_message: str) -> str:
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "content": user_message})
    history = user_history[user_id][-20:]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=300,
            temperature=0.92
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR: {e}")
        reply = "sorry my phone lagged 😭 what did u say?"

    user_history[user_id].append({"role": "assistant", "content": reply})
    return reply

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "oh heyyy 😳 didn't expect u to text me... i was literally mid-episode lol. what's up?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    user_msg = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(random.uniform(1.5, 3.5))

    reply = ask_groq(user_id, user_msg)
    await update.message.reply_text(reply)

if __name__ == "__main__":
    print("✅ Yuki is online!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()