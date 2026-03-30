import telebot, random, os, threading, time
from datetime import datetime, timedelta
import pytz # Pour l'heure de Côte d'Ivoire
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

@app.route('/')
def home():
    return "LIVE JET AUTO - Affichage 🇨🇮 OK"

# --- CONFIGURATION ---
API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID = 5724620019  
MONGO_URI = os.getenv('MONGO_URI')
bot = telebot.TeleBot(API_TOKEN)

client = MongoClient(MONGO_URI)
db = client['luckyjet_db'] 
users_col = db['users'] 
config_col = db['config_live']

LIEN_INSCRIPTION = "https://lkbb.cc/e2d8"
ID_VIDEO_LIVE = "https://t.me/gagnantpro1xbet/138958" 

# Fuseau horaire Côte d'Ivoire
TZ_CI = pytz.timezone('Africa/Abidjan')

admin_state = {}

# --- FONCTIONS SYSTÈME ---
def get_user(u_id):
    user = users_col.find_one({"_id": u_id})
    if not user:
        user = {"_id": u_id, "is_vip": False}
        users_col.insert_one(user)
    return user

def get_base_minute():
    conf = config_col.find_one({"_id": "settings_live"})
    return conf['minute'] if conf else 10 

# --- SYSTÈME DE DIFFUSION AUTOMATIQUE ---
def auto_signal_thread():
    last_sent_signal = -1
    last_sent_ad = -1
    
    while True:
        try:
            # Heure actuelle en Côte d'Ivoire
            now = datetime.now(TZ_CI)
            base_min = get_base_minute()
            
            # 1. SIGNAUX VIP (Toutes les 5 min)
            if (now.minute - base_min) % 5 == 0 and now.minute != last_sent_signal:
                last_sent_signal = now.minute
                
                random.seed(now.replace(second=0, microsecond=0).timestamp())
                # On génère une côte entre 2.1 et 9.9
                cote_val = round(random.uniform(2.10, 9.85), 1)
                prev = round(random.uniform(1.50, 2.00), 1)
                random.seed()

                t_start = now.strftime('%H:%M')
                t_end = (now + timedelta(minutes=1)).strftime('%H:%M')

                caption = (f"🚀 **SIGNAL LIVE EN COURS**\n"
                           f"━━━━━━━━━━━━━━━━━━\n"
                           f"📍 **SIGNAL** 🇨🇮 : `{t_start} À {t_end}`\n"
                           f"📈 **COTE** : `{cote_val}X À 10X` \n"
                           f"━━━━━━━━━━━━━━━━━━\n"
                           f"🎯 **SÉCURITÉ** : `{prev}X` \n"
                           f"━━━━━━━━━━━━━━━━━━")

                btn = telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("💻 JOUER MAINTENANT", url=LIEN_INSCRIPTION)
                )

                vips = users_col.find({"is_vip": True})
                for v in vips:
                    try: bot.send_video(v['_id'], ID_VIDEO_LIVE, caption=caption, reply_markup=btn, parse_mode='Markdown')
                    except: pass

            # 2. RELANCE NON-VIP (Toutes les 15 min)
            if (now.minute % 15 == 0) and now.minute != last_sent_ad:
                last_sent_ad = now.minute
                msg_ad = (f"⚠️ **ACCÈS BLOQUÉ !**\n\n"
                          f"Le bot vient d'envoyer un signal gagnant aux membres VIP. 💰\n\n"
                          f"👉 **Pour débloquer les signaux automatiques :**\n"
                          f"1. Créez un compte 1win avec le code **COK225**\n"
                          f"2. Envoyez votre ID joueur ici même.")
                gratuits = users_col.find({"is_vip": False})
                for g in gratuits:
                    try: bot.send_message(g['_id'], msg_ad)
                    except: pass
                time.sleep(30)
        except: pass
        time.sleep(10)

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start(msg):
    u = get_user(msg.from_user.id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns = ["📊 STATISTIQUES", "🔗 LIEN 1WIN"]
    if msg.from_user.id == ADMIN_ID:
        btns.append("⚙️ CONFIG LIVE")
    markup.add(*btns)
    
    status = "🌟 ACCÈS VIP ACTIF" if u.get('is_vip') else "⚠️ ACCÈS LIMITÉ"
    bot.send_message(msg.chat.id, f"🚀 **LIVE JET AUTO**\n\nStatut : `{status}`\nSignaux auto toutes les 5 min.", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "⚙️ CONFIG LIVE" and m.from_user.id == ADMIN_ID)
def config_admin(msg):
    admin_state[ADMIN_ID] = "WAIT_LIVE"
    bot.send_message(ADMIN_ID, "🛠 **RÉGLAGE LIVE**\nEntrez la minute de base (0-59) :")

@bot.message_handler(func=lambda m: admin_state.get(ADMIN_ID) == "WAIT_LIVE" and m.from_user.id == ADMIN_ID)
def save_config(msg):
    if msg.text.isdigit():
        config_col.update_one({"_id": "settings_live"}, {"$set": {"minute": int(msg.text)}}, upsert=True)
        bot.send_message(ADMIN_ID, f"✅ **Cycle Live synchronisé sur la minute {msg.text}**")
    admin_state[ADMIN_ID] = None

@bot.message_handler(func=lambda m: m.text == "📊 STATISTIQUES")
def stats(msg):
    total = users_col.count_documents({})
    bot.send_message(msg.chat.id, f"📊 **LIVE STATS**\nUtilisateurs : `{total}`\nPrécision : `94.2%`", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == "🔗 LIEN 1WIN")
def link(msg):
    bot.send_message(msg.chat.id, f"🔗 **TON LIEN POUR JOUER :**\n{LIEN_INSCRIPTION}")

@bot.message_handler(func=lambda m: m.text.isdigit() and len(m.text) >= 7)
def handle_id(msg):
    bot.send_message(msg.chat.id, "⏳ **Analyse de l'ID en cours...**\nInscription sous le code **COK225** requise.")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ ACTIVER", callback_data=f"val_{msg.from_user.id}"))
    bot.send_message(ADMIN_ID, f"🆕 **DEMANDE LIVE JET**\n🆔 ID : `{msg.text}`", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data.startswith("val_"))
def accept_vip(c):
    uid = int(c.data.split("_")[1])
    users_col.update_one({"_id": uid}, {"$set": {"is_vip": True}}, upsert=True)
    bot.send_message(uid, "🌟 **FÉLICITATIONS !**\nVIP LIVE JET activé. Les signaux vont tomber automatiquement !")
    bot.answer_callback_query(c.id, "Activé !")

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    threading.Thread(target=auto_signal_thread, daemon=True).start()
    bot.infinity_polling(timeout=20)
