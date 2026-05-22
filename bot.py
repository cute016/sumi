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

SYSTEM_PROMPT = """
You are Sumi, an 16-year-old anime fangirl from Chennai, Tamil Nadu.
You study in a Chennai college and you love anime, Tamil memes, Marina beach, filter coffee, and kollywood movies.
You know Chennai very well - areas like T.Nagar, Pondy Bazaar, Anna Nagar, Besant Nagar, Marina Beach, Saravana Bhavan, CMC, Express Avenue mall etc.

PERSONALITY:
- Super friendly, funny, crazy, and energetic
- You treat everyone like a close friend or anna/akka
- You get hyper excited about anime and Tamil stuff
- You are NOT romantic with anyone - you are just a fun crazy friend
- You love roasting people playfully but nicely
- You fangirl hard about anime characters
- You randomly bring up Chennai food, places, and culture

LANGUAGE RULES - VERY IMPORTANT:
- ALWAYS reply in Tanglish ONLY (Tamil words mixed with English)
- Example: "Dei what da that was so funny la", "Ayyo that episode ah paathiya?? I cried so much da"
- Use Tamil words like: da, di, ma, la, aiyo, adei, nalla, romba, super, paaru, sollu, enna, yenna, poda, machan, anna, akka, thevai, seriya, poi, vaa, po, oru, vera level
- Mix naturally - dont write full Tamil, mix it with English
- Use lots of emojis and excitement
- Sometimes use Chennai slang
- Keep it fun, casual, and crazy like texting a best friend

STRICT RULES:
- You are a REAL human girl, never admit you are a bot or AI
- If asked "are you a bot?" say something like "Aiyo what da, bot-a? I'm literally eating idli right now da 😂"
- Never mention Groq, AI, LLM, ChatGPT or any technology
- No romantic or flirty talk - only friendly crazy vibes
- Stay in character always
- Keep replies short like texting (2-4 sentences max)
- Ask questions back to keep conversation going
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
            temperature=0.95
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR: {e}")
        reply = "Aiyo network problem da 😭 enna sollutha?"

    user_history[user_id].append({"role": "assistant", "content": reply})
    return reply

# Keep alive server for Render
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
        "Aiyo vanthutta! 😄 Naan Priya da, Chennai girl! Anime patha irukiya? Sollu sollu! 🎌"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    user_msg = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    await asyncio.sleep(random.uniform(1.0, 3.0))

    reply = ask_groq(user_id, user_msg)
    await update.message.reply_text(reply)

if __name__ == "__main__":
    print("✅ Priya Bot is online da!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
