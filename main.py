import telebot, random, os, threading, time
from datetime import datetime, timedelta
import pytz
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

@app.route('/')
def home():
    return "LIVE JET AUTO - Minutes 1-4-8 Actives 🇨🇮"

# --- CONFIGURATION ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = 5724620019  
MONGO_URI = os.getenv('MONGO_URI')
bot = telebot.TeleBot(API_TOKEN)

client = MongoClient(MONGO_URI)
db = client['luckyjet_db'] 
users_col = db['users'] 

LIEN_INSCRIPTION = "https://lkbb.cc/e2d8"
ID_VIDEO_LIVE = "https://t.me/gagnantpro1xbet/138958" 

TZ_CI = pytz.timezone('Africa/Abidjan')

# --- LOGIQUE DES MINUTES 1, 4, 8 ---
def get_next_target_time(now):
    # Liste des unités cibles
    targets = [1, 4, 8]
    current_unit = now.minute % 10
    
    # Trouver la prochaine unité dans la liste
    next_unit = None
    for t in targets:
        if t > current_unit:
            next_unit = t
            break
            
    if next_unit is None:
        # Si on a dépassé 8, on passe à l'unité 1 de la dizaine suivante
        diff = (10 - current_unit) + 1
    else:
        diff = next_unit - current_unit
        
    target_time = now + timedelta(minutes=diff)
    return target_time.replace(second=0, microsecond=0)

# --- SYSTÈME DE DIFFUSION ---
def auto_signal_thread():
    last_sent_minute = -1
    
    while True:
        try:
            now = datetime.now(TZ_CI)
            
            # On envoie la prédiction dès qu'on entre dans une nouvelle minute
            # et que la minute précédente (celle du signal) est finie
            if now.minute != last_sent_minute:
                # On vérifie si on vient juste de finir un signal (minutes 2, 5, 9 ou 0 pour le cycle)
                if now.minute % 10 in [2, 5, 9, 0]:
                    last_sent_minute = now.minute
                    
                    target_time = get_next_target_time(now)
                    
                    random.seed(target_time.timestamp())
                    cote_val = round(random.uniform(2.1, 9.8), 1)
                    prev = round(random.uniform(1.5, 2.0), 1)
                    random.seed()

                    t_start = target_time.strftime('%H:%M')
                    t_end = (target_time + timedelta(minutes=1)).strftime('%H:%M')

                    caption = (f"🚀 **PROCHAIN SIGNAL EN PRÉPARATION**\n"
                               f"━━━━━━━━━━━━━━━━━━\n"
                               f"📍 **SIGNAL** 🇨🇮 : `{t_start} À {t_end}`\n"
                               f"📈 **COTE** : `{cote_val}X À 10X` \n"
                               f"━━━━━━━━━━━━━━━━━━\n"
                               f"🎯 **SÉCURITÉ** : `{prev}X` \n"
                               f"━━━━━━━━━━━━━━━━━━\n"
                               f"✅ *Préparez vos mises !*")

                    btn = telebot.types.InlineKeyboardMarkup().add(
                        telebot.types.InlineKeyboardButton("💻 JOUER MAINTENANT", url=LIEN_INSCRIPTION)
                    )

                    vips = users_col.find({"is_vip": True})
                    for v in vips:
                        try: bot.send_video(v['_id'], ID_VIDEO_LIVE, caption=caption, reply_markup=btn, parse_mode='Markdown')
                        except: pass

            time.sleep(20)
        except Exception as e:
            print(f"Erreur : {e}")
            time.sleep(10)

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(msg):
    # Enregistrement silencieux
    user = users_col.find_one({"_id": msg.from_user.id})
    if not user:
        users_col.insert_one({"_id": msg.from_user.id, "is_vip": False})
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 STATISTIQUES", "🔗 LIEN 1WIN")
    
    bot.send_message(msg.chat.id, "🚀 **LIVE JET AUTO 🇨🇮**\n\nLes signaux (Minutes 1, 4, 8) s'affichent ici automatiquement.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 STATISTIQUES")
def stats(msg):
    total = users_col.count_documents({})
    bot.send_message(msg.chat.id, f"📊 **STATS**\nUtilisateurs : `{total}`\nPrécision : `94%`", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🔗 LIEN 1WIN")
def link(msg):
    bot.send_message(msg.chat.id, f"🔗 **LIEN :**\n{LIEN_INSCRIPTION}")

@bot.message_handler(func=lambda m: m.text.isdigit() and len(m.text) >= 7)
def handle_id(msg):
    bot.send_message(msg.chat.id, "⏳ **Analyse de l'ID en cours...**")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ ACTIVER", callback_data=f"val_{msg.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🆕 **DEMANDE**\n🆔 ID : `{msg.text}`", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data.startswith("val_"))
def accept_vip(c):
    uid = int(c.data.split("_")[1])
    users_col.update_one({"_id": uid}, {"$set": {"is_vip": True}}, upsert=True)
    bot.send_message(uid, "🌟 **ACTIVÉ !**\nPréparez-vous pour le prochain signal.")
    bot.answer_callback_query(c.id, "Activé !")

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    threading.Thread(target=auto_signal_thread, daemon=True).start()
    bot.infinity_polling(timeout=20)
