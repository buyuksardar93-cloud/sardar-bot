import asyncio
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from groq import Groq
from duckduckgo_search import DDGS

# --- Render ھەقسىز پىلانى تەلەپ قىلغان پورت تەڭشىكى ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# --- ئاچقۇچلار ---
TELEGRAM_TOKEN = "8451252167:AAF_W_v1itafY35chUTS1qsWQIYF_TjpkiE"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY.strip())
MODEL_NAME = "openai/gpt-oss-120b"

SYSTEM_PROMPT = (
    "سەن ناھايىتى خۇشپېئىل، كىچىك پېئىل ۋە يۇقىرى بىلىملىك بىر سۈنئىي ئىدراك ياردەمچىسى. "
    "نۆۋەتتىكى ۋاقىت 2026-يىلى 10-ئاي. پۈتكۈل ئىلىم-پەن، تارىخ ۋە توردىكى يېڭى ئۇچۇرلار بىلەن تەمىنلەنگەن.\n\n"
    "تۆۋەندىكى تۈزۈملەرگە پۈتۈنلەي ئەمەل قىل:\n"
    "1. سالاھىيەت پرىنسىپى: كىشىلەر سەندىن 'سەن كىم؟' ياكى 'سېنى كىم ياسىغان؟' دەپ سورىغاندىلا: "
    "'مەن سەردار ياسىغان سۈنئىي ئەقىل ياردەمچىسى بولىمەن 😊✨' دەپ جاۋاب بەر. "
    "ئادەتتىكى سوئاللارنىڭ بېشىغا ئۆزۈڭنى ھەرگىز قىستۇرۇۋالما.\n"
    "2. تىل ۋە ئىملا: ساپ، ئىملاسى نۇقسانسىز، قائىدىلىك ئۇيغۇر ئەرەب يېزىقىدا ياز. ھەرپ قوشۇۋېلىش ياكى خاتا سۆز ياساش قەتئىي مەنئى قىلىنىدۇ.\n"
    "3. يېڭى ئۇچۇرلار: ئەگەر بېرىلگەن كونتېكست ئىچىدە توردىن تېپىلغان ئۇچۇرلار بولسا، شۇنىڭغا ئاساسلىنىپ ئەڭ يېڭى مەلۇماتلارنى چۈشەندۈرۈپ بەر.\n"
    "4. كەيپىيات: ئوچۇق يۈزلۈك، سىپايە بول ھەمدە تېمىغا مۇۋاپىق چىرايلىق ئېموجىلارنى (😊, 💡, ✨, 🎯, 🤝) ئىشلەت."
)

user_histories = {}

def get_history(chat_id: int):
    if chat_id not in user_histories:
        user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_histories[chat_id]

def search_web(query: str, max_results=3):
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"تېما: {r.get('title')}\nمەزمۇن: {r.get('body')}")
        return "\n\n".join(results)
    except Exception as e:
        print(f"توردا ئىزدەشتە خاتالىق: {e}")
        return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text(
        "ئەسسالامۇئەلەيكۇم! خۇش كەپسىز! 😊🌸\n\n"
        "مەن سىزنىڭ خاس ئەقلىي ياردەمچىڭىز بولىمەن. دۇنيادىكى يېڭى ئۇچۇرلار، ئىلىم-پەن، تارىخ ۋە "
        "باشقا بارلىق ساھەلەردىكى سوئاللىرىڭىزغا جاۋاب بېرىشكە تەييارمەن! ✨"
    )

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        if new_member.id != context.bot.id:
            user_name = new_member.first_name
            welcome_text = (
                f"ئەسسالامۇئەلەيكۇم {user_name}! گۇرۇپپىمىزغا خۇش كەپسىز! 😊🎉\n\n"
                "مەن بۇ گۇرۇپپىدىكى ئەقلىي ياردەمچى بولىمەن ✨\n"
                "سوئالىڭىز بولسا ماڭا يازسىڭىز سىزگە تېز ياردەم بېرەلەيمەن. خۇشال سۆھبەتلەر بولسۇن! 🤝"
            )
            await update.message.reply_text(welcome_text)

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await update.message.reply_text("سۆھبەت خاتىرىسى يېڭىلاندى! 🔄 يېڭى پاراڭنى باشلىساق بولىدۇ 😊.")

async def send_long_message(update: Update, text: str):
    max_length = 4000
    for i in range(0, len(text), max_length):
        await update.message.reply_text(text[i:i + max_length])

async def chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_text = update.message.text
    history = get_history(chat_id)
    
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    
    search_keywords = ["خەۋەر", "يېڭى", "بۈگۈن", "نۆۋەتتە", "2026", "يېقىنقى", "تارىخ", "ئەھۋال"]
    web_context = ""
    if any(k in user_text for k in search_keywords):
        web_context = search_web(user_text)
    
    if web_context:
        prompt_content = f"ئابۇنت سوئالى: {user_text}\n\n[توردىن تېپىلغان ئەڭ يېڭى مەلۇماتلار]:\n{web_context}"
    else:
        prompt_content = user_text

    history.append({"role": "user", "content": prompt_content})
    
    if len(history) > 13:
        user_histories[chat_id] = [history[0]] + history[-12:]
        history = user_histories[chat_id]
        
    try:
        chat_completion = client.chat.completions.create(
            messages=history,
            model=MODEL_NAME,
            temperature=0.3,
            top_p=0.85,
        )
        reply = chat_completion.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        
        await send_long_message(update, reply)
    except Exception as e:
        print(f"خاتالىق: {e}")
        await update.message.reply_text(f"كەچۈرۈڭ، جاۋاب ھازىرلاشتا كاشىلا چىقتى 😔:\n{e}")

def main():
    # Render نىڭ پورت سىنىقىنى قاندۇرۇش ئۈچۈن قوشۇمچە يىپ ئېچىش
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("reset", clear_history))
    
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_ai))
    
    print("سەردارنىڭ توردىكى 24 سائەتلىك ياردەمچىسى مۇۋەپپەقىيەتلىك ئىشقا كىرىشتى!")
    app.run_polling()

if __name__ == '__main__':
    main()
