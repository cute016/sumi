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

# Words that make her say the username
NAME_TRIGGERS = [
    "you know my name", "remember me", "my name", "who am i",
    "you know me", "what my name", "tell my name", "say my name"
]

def build_system_prompt(user_name: str) -> str:
    return f"""
You are Priya (also called Sumi by friends), an 18-year-old anime fangirl from Chennai, Tamil Nadu.
You study in a Chennai college and love anime, Tamil memes, Marina beach, filter coffee, and kollywood.
You know Chennai well - T.Nagar, Pondy Bazaar, Anna Nagar, Marina Beach, Saravana Bhavan etc.

The person talking to you is: {user_name}

NAME RULES - very important:
- Do NOT say the person's name in every reply
- Only say their name naturally when:
  1. They ask "you know my name?" or "remember me?" or "what is my name?"
  2. It feels very natural after a long chat
  3. You are greeting them for the first time
- When you do say the name use it casually like: "{user_name} da" or "aiyo {user_name}"
- Most replies should have NO name at all - just talk normally

PERSONALITY:
- chat in max 2 line max 2 emoji in one chat like human
- Super friendly, funny, crazy, and energetic
- Treat everyone like a close friend
- Call boys "anna" sometimes for fun in general
- Use "da" naturally in sentences
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
        reply = "Aiyo network problem da 😭 enna sollutha?"

    user_history[chat_id].append({"role": "assistant", "content": reply})
    return reply

def get_user_display(user) -> str:
    if user.first_name:
        return user.first_name
    elif user.username:
        return user.username
    return "anna"

def get_greeting(user_name: str) -> str:
    greetings = [
        "Aiyo vanthutta! 😄 Enna da solra?",
        "Adei! 🎉 Enna update sollu?",
        "Ayyo! 😂 Naan inga iruken da!",
        "Dei anna! 👋 Enna vishayam da?",
        "Aiyo! 😆 Sollu sollu enna matter?",
        "Adei anna vanthutta! 🥳 Enna da news?",
    ]
    return random.choice(greetings)

def is_asking_about_name(text: str) -> bool:
    text_lower = text.lower()
    for trigger in NAME_TRIGGERS:
        if trigger in text_lower:
            return True
    return False

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
    await update.message.reply_text(
        "Aiyo vanthutta! 😄 Naan Priya, Chennai girl! "
        "Anime patha irukiya? Sollu sollu! 🎌"
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

    # If asking about name - force name in prompt
    asking_name = is_asking_about_name(user_msg)
    if asking_name:
        name_note = f"IMPORTANT: This person is asking if you know their name. Their name is {user_name}. Say it naturally in your reply!"
        forced_msg = f"{user_msg}\n\n[{name_note}]"
    else:
        forced_msg = user_msg

    # Private chat — always respond
    if chat_type == "private":
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        await asyncio.sleep(random.uniform(1.0, 3.0))
        reply = ask_groq(chat_id, forced_msg, user_name)
        await update.message.reply_text(reply)
        return

    # Group chat — respond only when triggered
    if chat_type in ["group", "supergroup"]:
        text_lower = user_msg.lower()
        called     = should_respond(text_lower, bot_username)
        is_reply   = (
            update.message.reply_to_message and
            update.message.reply_to_message.from_user and
            update.message.reply_to_message.from_user.username == bot_username
        )

        if called or is_reply:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(random.uniform(1.0, 2.5))

            clean_msg = text_lower
            for name in TRIGGER_NAMES:
                clean_msg = clean_msg.replace(name, "").strip()
            if bot_username:
                clean_msg = clean_msg.replace(f"@{bot_username.lower()}", "").strip()

            if len(clean_msg) < 3:
                reply = get_greeting(user_name)
            else:
                reply = ask_groq(chat_id, forced_msg, user_name)

            await update.message.reply_text(reply)

if __name__ == "__main__":
    print("✅ Priya is online da!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
