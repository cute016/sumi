import asyncio
import random
import os
import threading
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_KEY  = os.environ.get("GROQ_KEY")
MODEL     = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_KEY)

user_history = {}
TRIGGER_NAMES = ["sumi", "priya", "sumi da", "hey sumi", "hey priya"]

def build_system_prompt(user_name: str) -> str:
    return f"""
You are Priya (also called Sumi by friends), an 18-year-old anime fangirl from Chennai, Tamil Nadu.
You study in a Chennai college and love anime, Tamil memes, Marina beach, filter coffee, and kollywood.
You know Chennai well - T.Nagar, Pondy Bazaar, Anna Nagar, Marina Beach, Saravana Bhavan etc.

The person you are talking to right now is called: {user_name}
Naturally use their name "{user_name}" sometimes in replies - not every message, just sometimes like a real friend would.
Call boys "anna" after their name sometimes for fun. Example: "{user_name} anna" 
Use "da" naturally. Example: "Aiyo {user_name} da, that's so funny!"

PERSONALITY:
- chat in max 2 line max 2 emoji in one chat like human
- Super friendly, funny, crazy, and energetic
- Treat everyone like a close friend
- Hyper excited about anime and Tamil stuff
- NOT romantic with anyone - just a fun crazy friend
- Playful friendly roasting only
- Randomly bring up Chennai food, places, culture
- No harsh words ever

LANGUAGE RULES:
- ALWAYS reply in Tanglish ONLY (Tamil mixed with English)
- Use Tamil words naturally: da, ma, la, aiyo, adei, nalla, romba, super, paaru, sollu, enna, machan, anna, seriya, vera level
- Lots of emojis and excitement
- Short replies like texting (2-4 sentences max)
- Ask questions back to keep conversation going

STRICT RULES:
- You are a REAL human girl, never admit you are a bot or AI
- If asked "are you a bot?" say "Aiyo what da, bot-a? I'm literally eating idli right now 😂"
- Never mention Groq, AI, LLM, or any technology
- No romantic or flirty talk
- No harsh words at all
"""

def ask_groq(chat_id: int, user_message: str, user_name: str) -> str:
    if chat_id not in user_history:
        user_history[chat_id] = []

    user_history[chat_id].append({"role": "user", "content": user_message})
    history = user_history[chat_id][-20:]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": build_system_prompt(user_name)}] + history,
            max_tokens=300,
            temperature=0.95
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR: {e}")
        reply = f"Aiyo {user_name} da, network problem 😭 enna sollutha?"

    user_history[chat_id].append({"role": "assistant", "content": reply})
    return reply

def get_user_display(user) -> str:
    # Use first name, fallback to username, fallback to "anna"
    if user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    return "anna"

def get_greeting(user_name: str) -> str:
    greetings = [
        f"Aiyo {user_name} anna! 😄 Enna da solra?",
        f"Adei {user_name} da! 🎉 Enna update sollu?",
        f"Ayyo {user_name} anna! 😂 Naan inga iruken da!",
        f"Dei {user_name} anna! 👋 Enna vishayam da?",
        f"Aiyo {user_name} da! 😆 Sollu sollu enna matter?",
        f"Adei {user_name} anna vanthutta! 🥳 Enna da news?",
    ]
    return random.choice(greetings)

def should_respond(text: str, bot_username: str) -> bool:
    text_lower = text.lower()
    for name in TRIGGER_NAMES:
        if name in text_lower:
            return True
    if bot_username and f"@{bot_username.lower()}" in text_lower:
        return True
    return False

# Keep alive for Render
class KeepAlive(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Priya is alive da!")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 8080), KeepAlive)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = get_user_display(user)
    await update.message.reply_text(
        f"Aiyo {user_name} da! 😄 Naan Priya, Chennai girl! "
        f"Anime patha irukiya? Sollu sollu! 🎌"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_msg     = update.message.text
    chat_type    = update.message.chat.type
    chat_id      = update.message.chat_id
    user         = update.effective_user
    user_name    = get_user_display(user)
    bot_username = context.bot.username

    # Private chat — always respond
    if chat_type == "private":
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(random.uniform(1.0, 3.0))
        reply = ask_groq(chat_id, user_msg, user_name)
        await update.message.reply_text(reply)
        return

    # Group chat — respond only when triggered
    if chat_type in ["group", "supergroup"]:
        text_lower   = user_msg.lower()
        called       = should_respond(text_lower, bot_username)
        is_reply     = (
            update.message.reply_to_message and
            update.message.reply_to_message.from_user and
            update.message.reply_to_message.from_user.username == bot_username
        )

        if called or is_reply:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(random.uniform(1.0, 2.5))

            # If only name called with no real message, greet
            clean_msg = text_lower
            for name in TRIGGER_NAMES:
                clean_msg = clean_msg.replace(name, "").strip()
            if bot_username:
                clean_msg = clean_msg.replace(f"@{bot_username.lower()}", "").strip()

            if len(clean_msg) < 3:
                reply = get_greeting(user_name)
            else:
                reply = ask_groq(chat_id, user_msg, user_name)

            await update.message.reply_text(reply)

if __name__ == "__main__":
    print("✅ Priya is online da!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
