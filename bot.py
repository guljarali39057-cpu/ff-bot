AAFGEAdTD2RsOMxU49Au0UOQBLPmzoOswHg random
import time
import urllib.parse
import json
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

# Setup Configuration
BOT_TOKEN = "8367812316:AAE1FcbeFbsuCJ6t0t-9zp8cVJVLU6UD5Ug"
ADMIN_ID = 8487604781
ADMIN_USERNAME = "Gosjesg001"
UPI_ID = "maxff001@axl"  # Nayi UPI ID update kar di gayi hai

bot = telebot.TeleBot(BOT_TOKEN)

# JSON Database Setup (Permanent Storage)
DB_FILE = "coins_db.json"

def load_coins():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception:
            return {}
    return {}

def save_coins():
    with open(DB_FILE, "w") as f:
        json.dump(user_coins, f)

user_coins = load_coins()
pending_requests = {}  # req_id -> {user_id, coins, amount, status}
user_states = {}       # user_id -> {state, req_id}

def get_coins(user_id):
    return user_coins.get(int(user_id), 0)

def add_coins(user_id, amount):
    user_id = int(user_id)
    user_coins[user_id] = get_coins(user_id) + amount
    save_coins()

def deduct_coins(user_id, amount):
    user_id = int(user_id)
    user_coins[user_id] = max(0, get_coins(user_id) - amount)
    save_coins()

# /cancel command
@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        bot.reply_to(message, "❌ Process cancel kar diya gaya hai.")
    else:
        bot.reply_to(message, "Koi active process nahi tha.")

# Main Welcome Screen Function
def send_welcome_msg(chat_id, user_id, first_name):
    coins = get_coins(user_id)
    
    welcome_text = (
        f"Namaste {first_name}! 👋\n\n"
        f"💰 **Aapka Balance:** `{coins} COINS`\n\n"
        "Security Code generate karne ke liye niche button par click karein."
    )
    
    markup = InlineKeyboardMarkup()
    btn_code = InlineKeyboardButton(text="🔑 Security Code", callback_data="prompt_token")
    btn_my_coins = InlineKeyboardButton(text="👛 My Coins", callback_data="check_coins")
    btn_buy_coins = InlineKeyboardButton(text="💰 Buy Coins", callback_data="buy_coins")
    btn_help = InlineKeyboardButton(text="🛠 Help", callback_data="show_help")
    
    markup.add(btn_code)
    markup.add(btn_my_coins, btn_buy_coins)
    markup.add(btn_help)
    
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    send_welcome_msg(message.chat.id, message.from_user.id, message.from_user.first_name)

# Callback Query Handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    coins = get_coins(user_id)

    # My Coins Alert Pop-up
    if call.data == "check_coins":
        bot.answer_callback_query(
            call.id, 
            text=f"💳 Aapka Current Credit: {coins} COINS", 
            show_alert=True
        )

    # Buy Coins Selection Screen
    elif call.data == "buy_coins":
        bot.answer_callback_query(call.id)
        buy_text = (
            "╭─────────────────╮\n"
            "  💰 **BUY COINS** ✦\n"
            "╰─────────────────╯\n\n"
            "💳 **First select your payment method:**\n\n"
            "🇮🇳 **UPI – For India**\n"
            "🌐 **BINANCE – Other Countries / Servers**"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="🇮🇳 UPI – For India", callback_data="pay_upi"))
        markup.add(InlineKeyboardButton(text="🌐 BINANCE – Other Countries / Servers", callback_data="pay_binance"))
        markup.add(InlineKeyboardButton(text="🏠 MAIN MENU", callback_data="main_menu"))
        
        bot.send_message(call.message.chat.id, buy_text, parse_mode="Markdown", reply_markup=markup)

    # UPI Package Selection Menu
    elif call.data == "pay_upi":
        bot.answer_callback_query(call.id)
        pkg_text = "💳 **UPI PACKAGE SELECTION**\n\nSelect your package in INR:"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="🪙 10 COINS • ₹199", callback_data="buy_pkg_10_199"))
        markup.add(InlineKeyboardButton(text="🪙 25 COINS • ₹249", callback_data="buy_pkg_25_249"))
        markup.add(InlineKeyboardButton(text="🪙 50 COINS • ₹349", callback_data="buy_pkg_50_349"))
        markup.add(InlineKeyboardButton(text="🪙 100 COINS • ₹549", callback_data="buy_pkg_100_549"))
        markup.add(InlineKeyboardButton(text="🔄 CHANGE PAYMENT METHOD", callback_data="buy_coins"))
        markup.add(InlineKeyboardButton(text="❌ CLOSE", callback_data="close_msg"))
        
        bot.send_message(call.message.chat.id, pkg_text, parse_mode="Markdown", reply_markup=markup)

    # Package Clicked (Shows QR Code & Payment Details)
    elif call.data.startswith("buy_pkg_"):
        bot.answer_callback_query(call.id)
        try:
            parts = call.data.split("_")
            coins_qty = int(parts[2])
            amount = int(parts[3])
            
            req_id = random.randint(100, 999)
            pending_requests[req_id] = {
                'user_id': user_id,
                'coins': coins_qty,
                'amount': amount,
                'status': 'PENDING'
            }
            
            upi_pay_url = f"upi://pay?pa={UPI_ID}&pn=Admin&am={amount}&cu=INR"
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_pay_url)}"
            
            caption_text = (
                "💳 **COIN PAYMENT — UPI (INDIA)**\n"
                "─────────────────────────────\n\n"
                f"🪙 **Package:** {coins_qty} COINS\n"
                f"💵 **Amount:** ₹{amount}\n\n"
                f"📱 **UPI ID:** `{UPI_ID}` *(Tap to copy)*\n\n"
                "📲 **QR Code scan karke payment karein.**\n\n"
                "⚠️ **Payment karne ke baad SEND PAYMENT SCREENSHOT button par click karke screenshot bhej dein.**\n\n"
                f"🧾 **Request ID:** `#{req_id}`\n"
                "─────────────────────────────"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text="📸 SEND PAYMENT SCREENSHOT", callback_data=f"init_screenshot_{req_id}"))
            markup.add(InlineKeyboardButton(text="🔄 SELECT NEW PKG / PAYMENT METHOD", callback_data="buy_coins"))
            markup.add(InlineKeyboardButton(text="🏠 MAIN MENU", callback_data="main_menu"))
            
            try:
                bot.send_photo(call.message.chat.id, photo=qr_api_url, caption=caption_text, parse_mode="Markdown", reply_markup=markup)
            except Exception:
                bot.send_message(call.message.chat.id, caption_text, parse_mode="Markdown", reply_markup=markup)

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Error: {str(e)}")

    # Prompt user to send payment screenshot
    elif call.data.startswith("init_screenshot_"):
        bot.answer_callback_query(call.id)
        req_id = int(call.data.split("_")[2])
        
        req_info = pending_requests.get(req_id)
        if not req_info:
            bot.send_message(call.message.chat.id, "❌ Request expire ho chuka hai.")
            return

        user_states[user_id] = {'state': 'WAITING_SCREENSHOT', 'req_id': req_id}
        
        prompt_text = (
            "📸 **SEND PAYMENT SCREENSHOT**\n\n"
            f"🧾 **Request ID:** `#{req_id}`\n"
            f"🪙 **Coins:** {req_info['coins']}\n"
            f"💵 **Amount:** ₹{req_info['amount']}\n\n"
            "👉 **Apna successful payment ka screenshot bhej dein.**\n\n"
            "❌ **Cancel karne ke liye /cancel likhein.**"
        )
        bot.send_message(call.message.chat.id, prompt_text, parse_mode="Markdown")

    # Admin Approve Action
    elif call.data.startswith("approve_"):
        bot.answer_callback_query(call.id)
        req_id = int(call.data.split("_")[1])
        req_info = pending_requests.get(req_id)
        
        if req_info and req_info['status'] == 'PENDING':
            target_user = req_info['user_id']
            added_coins = req_info['coins']
            
            add_coins(target_user, added_coins)
            req_info['status'] = 'APPROVED'
            
            user_markup = InlineKeyboardMarkup()
            user_markup.add(InlineKeyboardButton(text="🏠 MAIN MENU", callback_data="main_menu"))
            
            bot.send_message(
                target_user,
                f"🎉 **PAYMENT APPROVED!**\n\n"
                f"🧾 Request ID: `#{req_id}`\n"
                f"🪙 `{added_coins} COINS` aapke wallet me add kar diye gaye hain!\n"
                f"💰 Total Balance: `{get_coins(target_user)} COINS`",
                parse_mode="Markdown",
                reply_markup=user_markup
            )
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"✅ **APPROVED**\nRequest ID: #{req_id}\nAdded {added_coins} coins to User `{target_user}`.",
                parse_mode="Markdown"
            )

    # Admin Reject Action
    elif call.data.startswith("reject_"):
        bot.answer_callback_query(call.id)
        req_id = int(call.data.split("_")[1])
        req_info = pending_requests.get(req_id)
        
        if req_info and req_info['status'] == 'PENDING':
            target_user = req_info['user_id']
            req_info['status'] = 'REJECTED'
            
            user_markup = InlineKeyboardMarkup()
            user_markup.add(InlineKeyboardButton(text="🏠 MAIN MENU", callback_data="main_menu"))
            
            bot.send_message(
                target_user,
                f"❌ **PAYMENT REJECTED**\n\n"
                f"Aapki Request ID `#{req_id}` reject kar di gayi hai.",
                parse_mode="Markdown",
                reply_markup=user_markup
            )
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=f"❌ **REJECTED**\nRequest ID: #{req_id}",
                parse_mode="Markdown"
            )

    # Binance Option
    elif call.data == "pay_binance":
        bot.answer_callback_query(call.id)
        binance_text = "🌐 **BINANCE PAYMENT**\n\nCrypto/Binance Pay ke zariye Coins lene ke liye Admin ko contact karein."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="💬 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}"))
        markup.add(InlineKeyboardButton(text="🔄 CHANGE PAYMENT METHOD", callback_data="buy_coins"))
        bot.send_message(call.message.chat.id, binance_text, parse_mode="Markdown", reply_markup=markup)

    # Main Menu
    elif call.data == "main_menu":
        bot.answer_callback_query(call.id)
        send_welcome_msg(call.message.chat.id, call.from_user.id, call.from_user.first_name)

    # Security Code Action
    elif call.data == "prompt_token":
        required_coins = 10
        if coins < required_coins:
            bot.answer_callback_query(call.id, text="Coins kam hain!", show_alert=True)
            insufficient_text = (
                "╭─────────────────╮\n"
                "  🪙 **INSUFFICIENT COINS** ✨\n"
                "╰─────────────────╯\n\n"
                f"💰 **Your Balance:** `{coins} COINS`\n"
                f"🔐 **Required:** `{required_coins} COIN`\n\n"
                "👉 Please use 💰 **BUY COINS** to request more coins from admin."
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(text="💰 Buy Coins", callback_data="buy_coins"))
            markup.add(InlineKeyboardButton(text="👛 My Coins", callback_data="check_coins"))
            bot.send_message(call.message.chat.id, insufficient_text, parse_mode="Markdown", reply_markup=markup)
            return

        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id, 
            "📌 **Apna Access Token yahan paste / send karein:**", 
            parse_mode="Markdown",
            reply_markup=ForceReply(selective=True)
        )
        bot.register_next_step_handler(msg, process_token)

    elif call.data == "show_help":
        bot.answer_callback_query(call.id, text="💡 Help: '🔑 Security Code' button par click karke token bhej dein.", show_alert=True)

    elif call.data == "close_msg":
        bot.answer_callback_query(call.id)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

# Photo Handler for Screenshot Verification
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    
    if user_id in user_states and user_states[user_id].get('state') == 'WAITING_SCREENSHOT':
        req_id = user_states[user_id]['req_id']
        req_info = pending_requests.get(req_id)
        
        del user_states[user_id]
        
        if not req_info:
            bot.reply_to(message, "❌ Invalid or expired Request ID.")
            return

        sent_msg = (
            "✅ **PAYMENT SCREENSHOT SENT**\n\n"
            f"🧾 **Request ID:** `#{req_id}`\n"
            "⏳ **Admin aapki payment verify karke coins add kar dega.**"
        )
        bot.reply_to(message, sent_msg, parse_mode="Markdown")
        
        photo_file_id = message.photo[-1].file_id
        admin_caption = (
            f"📥 **NEW PAYMENT PROOF RECEIVED**\n\n"
            f"👤 **User:** {message.from_user.first_name} (@{message.from_user.username or 'N/A'})\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🧾 **Request ID:** `#{req_id}`\n"
            f"🪙 **Coins:** `{req_info['coins']}`\n"
            f"💵 **Amount:** `₹{req_info['amount']}`"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{req_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{req_id}")
        )
        
        try:
            bot.send_photo(ADMIN_ID, photo=photo_file_id, caption=admin_caption, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            print(f"Admin message error: {e}")

# Token Processing
def process_token(message):
    user_id = message.from_user.id
    coins = get_coins(user_id)
    required_coins = 10
    
    if coins < required_coins:
        bot.reply_to(message, "❌ Aapke paas zaroori coins nahi hain.")
        return

    deduct_coins(user_id, required_coins)
    access_token = message.text.strip()
    
    loading_msg = bot.reply_to(
        message, 
        "⏳ **Processing Started... Please wait (10 minutes)**\n\nProgress: `[░░░░░░░░░░] 0%`", 
        parse_mode="Markdown"
    )
    
    for percent in range(5, 105, 5):
        time.sleep(6)
        filled = percent // 10
        unfilled = 10 - filled
        bar = "█" * filled + "░" * unfilled
        try:
            bot.edit_message_text(
                chat_id=loading_msg.chat.id,
                message_id=loading_msg.message_id,
                text=f"⏳ **Security Code Fetching...**\n\nProgress: `[{bar}] {percent}%`",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    random_security_code = random.randint(100000, 999999)
    response_text = (
        f"🔐 **Free Fire Security Code Result**\n\n"
        f"📌 **Access Token:** `{access_token[:15]}...`\n"
        f"🔑 **Security Code:** `{random_security_code}`\n"
        f"🪙 **Remaining Balance:** `{get_coins(user_id)} COINS`\n\n"
        f"⚡ Status: Completed Successfully"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="❌ Close", callback_data="close_msg"))
    
    bot.edit_message_text(
        chat_id=loading_msg.chat.id,
        message_id=loading_msg.message_id,
        text=response_text,
        parse_mode="Markdown",
        reply_markup=markup
    )

print("Bot active ho gaya hai...")
bot.infinity_polling()
