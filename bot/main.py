import os, re, time
import pandas as pd
import random
import telebot
import sqlite3
import string
import traceback
import threading
from confings import *
from telebot.types import InputMediaVideo
from threading import Timer
from buttons import *
from env import settings
from telebot import types
from jdatetime import datetime as jdatetime
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from collections import defaultdict
from datetime import timedelta


percentage_offer = defaultdict(dict)
stop_event = threading.Event()

ADMIN_CHAT_ID = "-1002422321851"

card_payments_group = "-1002255405490"
zarin_payments_group = "-1002408286014"
site_admin_group = "-1002262147601"

offer_broadcast_data = {}

temp_data = {}
admin_states = {}
delete_states = {}
user_states = {}
keyboards = {}
contents = {}
user_data = {}
current_pages = {}
temp_offer = {}
user_last_message = {}

bot = telebot.TeleBot(settings.token)

def save_info(user_id, first_name, last_name, chat_id, user_name):
    try:
        update_block_list(chat_id, "delete")
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                            chat_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            phone_number TEXT,
                            verify TEXT,
                            first_name TEXT,
                            last_name TEXT,
                            user_name TEXT,
                            join_date TEXT
                         )''')
            
            c.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
            existing_user = c.fetchone()

            if existing_user:
                c.execute("""UPDATE users SET first_name=?, last_name=?, user_name=?, user_id=? WHERE chat_id=?""",
                          (first_name, last_name, user_name, user_id, chat_id))
                bot.send_message(settings.customers_starts_2, 
    text=f"""
🔔Activation NEWS

<b>👤Name: </b> {first_name} {last_name}
<b>👤Chat: </b> <code>{chat_id}</code>
<b>👤User Name: </b> @{user_name}
<b>☎️User's chat ID: </b> <code>{user_id}</code>
""",
    parse_mode="HTML"
)

            else:
                join_date = str(get_current_date())
                c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                          (chat_id, user_id, None, None, first_name, last_name, user_name, join_date))
                bot.send_message(
                    settings.customers_starts_2, 
    text=f"""
🔔Activation NEWS

<b>👤Name: </b> {first_name} {last_name}
<b>👤Chat: </b> <code>{chat_id}</code>
<b>👤User Name: </b> @{user_name}
<b>☎️User's chat ID: </b> <code>{user_id}</code>
""",
    parse_mode="HTML"
)

            conn.commit()
    except sqlite3.Error as e:
        send_error_to_admin(traceback.format_exc())


def save_new_admin(admin_id, message):
    if admin_id == "برگشت 🔙":
        bot.send_message(message.chat.id, "به منوی ادمین برگشتید.", reply_markup=admin_markup)
    else:
        try:
            with sqlite3.connect(settings.database) as conn:
                c = conn.cursor()
                c.execute("BEGIN TRANSACTION")
                c.execute('''CREATE TABLE IF NOT EXISTS admin_list (
                                id INTEGER PRIMARY KEY,
                                admin_id INTEGER
                             )''')
                c.execute("INSERT INTO admin_list (admin_id) VALUES (?)", (admin_id,))
                conn.commit()
                bot.send_message(message.chat.id, "ادمین مورد نظر با موفقیت افزوده شد.", reply_markup=admin_markup)
        except Exception as e:
            bot.send_message(settings.matin, f"Error in save_new_admin: {e}")
            bot.send_message(message.chat.id, f"Error in save_new_admin: {e}")


def is_member_in_all_channels(chat_id):
    all_channels = get_all_channels()
    for channel_id in all_channels:
        member = bot.get_chat_member(channel_id, chat_id)
        if member.status not in ['member', 'administrator', 'creator']:
            return False
    return True


def get_all_channels():
    try:
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            c.execute("SELECT channel_id FROM channels")
            channels = [channel[0] for channel in c.fetchall() if channel[0] and str(channel[0]).startswith("-100")]
            return channels
    except Exception as e:
        send_error_to_admin(traceback.format_exc())
        return []


def delete_channel_by_id(channel_id):
    conn = sqlite3.connect(settings.database)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM channels WHERE id=?", (channel_id,))
        conn.commit()
        bot.send_message(settings.matin, f"Channel with id {channel_id} deleted successfully.")
    except Exception as e:
        conn.rollback()
        send_error_to_admin(traceback.format_exc())
    finally:
        conn.close()

def make_delete_channel_id_keyboard():
    try:
        conn = sqlite3.connect(settings.database)
        c = conn.cursor()

        c.execute("SELECT * FROM channels ORDER BY id")
        channel_info = c.fetchall()

        keyboard = []
        for channel in channel_info:
            channel_id, button_name, link_type, link, channel_chat_id = channel
            keyboard.append([InlineKeyboardButton(button_name, callback_data=f"delete_row_{channel_id}")])

        keyboard.append([InlineKeyboardButton("❌ خروج از منوی حذف کانال", callback_data=f"delete_button_1")])

        conn.close()
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        send_error_to_admin(traceback.format_exc())
        return None


def get_current_timestamp():
    return jdatetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_current_date():
    return jdatetime.now().strftime("%Y-%m-%d")


def search_all_users():
    conn = sqlite3.connect(settings.database)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_count = c.fetchone()[0]
    conn.close()
    return total_count


def make_delete_admin_list_keyboard():
    try:
        conn = sqlite3.connect(settings.database)
        c = conn.cursor()

        c.execute("SELECT * FROM admin_list ORDER BY id")
        latest_news = c.fetchall()

        keyboard = []
        for news in latest_news:
            news_id, post_title = news
            keyboard.append([InlineKeyboardButton(post_title, callback_data=f"delete_row_admin_{news_id}")])

        keyboard.append([InlineKeyboardButton("❌ خروج از منوی حذف ادمین", callback_data=f"delete_button_1")])

        conn.close()
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        bot.send_message(settings.matin, f"Error in creating make_delete_admin_list_keyboard: {e}")
        return None


def check_admin_id_exists(admin_id):
    conn = sqlite3.connect(settings.database)  
    c = conn.cursor()
    
    c.execute('SELECT 1 FROM crush_admin_info WHERE admin_id = ?', (admin_id,))
    result = c.fetchone()    
    conn.close()
    return result is not None





def is_member_channel(chat_id, channel_id):
    member = bot.get_chat_member(channel_id, chat_id)
    if member.status not in ['member', 'administrator', 'creator']:
        return False
    return True



def get_button_name(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    name = message.text.strip()
    if len(name) > 40:
        msg = bot.send_message(chat_id, "نام دکمه نباید بیشتر از ۴۰ کاراکتر باشد. لطفاً مجدداً ارسال کنید:", reply_markup=back_markup)
        bot.register_next_step_handler(msg, get_button_name)
        return
    temp_data[chat_id]['button_name'] = name
    msg = bot.send_message(chat_id, "لینک شما برای تلگرام است یا سایر موارد؟", reply_markup=create_selection_markup())
    bot.register_next_step_handler(msg, handle_link_type)
    

def handle_link_type(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    selection = message.text.strip()
    temp_data[chat_id]["link_type"] = selection
    
    if selection == "تلگرام":
        msg = bot.send_message(chat_id, "باشه! پس اول لینک یا آیدی اون کانال یا گروه تلگرامی رو برام بفرست و حواست باشه ربات رو توی اون کانال یا گروه ادمین کرده باشی.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, get_telegram_link)
    elif selection == "سایر موارد":
        msg = bot.send_message(chat_id, "لینک سایت، ربات، اینستاگرام، یا هر لینک دیگری که مدنظرتون هست رو ارسال کنید:", reply_markup=back_markup)
        bot.register_next_step_handler(msg, get_other_link)

def get_telegram_link(message):
    if check_return_2(message):
        return
    

    chat_id = message.chat.id
    link = message.text.strip()
    if link.startswith("@"): 
        link = f"https://t.me/{link[1:]}"
    elif not re.match(r"^https://t.me/\S+$", link):
        msg = bot.send_message(chat_id, "لینک یا آیدی معتبر ارسال کنید:", reply_markup=back_markup)
        bot.register_next_step_handler(msg, get_telegram_link)
        return
    temp_data[chat_id]['link'] = link
    msg = bot.send_message(chat_id, "یک پیام از آن کانال به من فوروارد کن یا آیدی عددی آن را بفرست (باید با -100 شروع شود):", reply_markup=back_markup)
    bot.register_next_step_handler(msg, get_telegram_id)

def get_telegram_id(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    if message.forward_from_chat:
        temp_data[chat_id]["channel_id"] = message.forward_from_chat.id
    elif message.text.startswith("-100"):
        temp_data[chat_id]["channel_id"] = message.text.strip()
    else:
        msg = bot.send_message(chat_id, "آیدی عددی باید با -100 شروع شود. لطفاً مجدداً ارسال کنید:", reply_markup=back_markup)
        bot.register_next_step_handler(msg, get_telegram_id)
        return
    save_data(chat_id)

def get_other_link(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    temp_data[chat_id]["link"] = message.text.strip()
    save_data(chat_id)

def save_data(chat_id):
    try:
        data = temp_data.get(chat_id, {})
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            c.execute("BEGIN TRANSACTION")
            c.execute('''CREATE TABLE IF NOT EXISTS channels (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            button_name TEXT NOT NULL,
                            link_type TEXT NOT NULL,
                            link TEXT NOT NULL,
                            channel_id TEXT
                         )''')
            c.execute("INSERT INTO channels (button_name, link_type, link, channel_id) VALUES (?, ?, ?, ?)",
                      (data.get("button_name"), data.get("link_type"), data.get("link"), data.get("channel_id")))
            conn.commit()
        bot.send_message(chat_id, "✅ اطلاعات با موفقیت ذخیره شد.", reply_markup=admin_markup)
        del temp_data[chat_id]
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا در ذخیره اطلاعات", reply_markup=admin_markup)
        bot.send_message(settings.matin, f"❌ خطا در ذخیره اطلاعات: {e}", reply_markup=admin_markup)

def create_selection_markup():
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row("تلگرام", "سایر موارد")
    markup.row("برگشت 🔙")
    return markup


def delete_admin_by_id(admin_id):
    conn = sqlite3.connect(settings.database)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM admin_list WHERE id=?", (admin_id,))
        conn.commit()
        bot.send_message(settings.matin, f"Channel with id {admin_id} deleted successfully.")
    except Exception as e:
        conn.rollback()
        bot.send_message(settings.matin, f"Error in delete_channel_by_id: {e}")
    finally:
        conn.close()

def get_admin_ids():
    return get_ids_from_db("admin_list", "admin_id")

def get_ids_from_db(table_name, column_name):
    try:
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            c.execute(f"SELECT {column_name} FROM {table_name}")
            ids = [row[0] for row in c.fetchall()]
            return ids
    except Exception as e:
        bot.send_message(settings.matin, f"Error in get_ids_from_db: {e}")
        return []
    


def create_block_list_table():
    with sqlite3.connect(settings.database) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS block_list (
                chat_id INTEGER PRIMARY KEY
            )
        """)
        conn.commit()
    
create_block_list_table()

def update_block_list(chat_id, operation):
    with sqlite3.connect(settings.database) as conn:
        c = conn.cursor()
        if operation.lower() == "add":
            c.execute("SELECT chat_id FROM block_list WHERE chat_id = ?", (chat_id,))
            result = c.fetchone()
            if not result:
                c.execute("INSERT INTO block_list (chat_id) VALUES (?)", (chat_id,))
                conn.commit()
                return True
            
        elif operation.lower() == "delete":
            c.execute("SELECT chat_id FROM block_list WHERE chat_id = ?", (chat_id,))
            result = c.fetchone()
            if result:
                c.execute("DELETE FROM block_list WHERE chat_id = ?", (chat_id,))
                conn.commit()
                return True

        else:
            return False
        

def confirm_send_all_users(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("✔ مطمئن هستم"))
    keyboard.add(types.KeyboardButton("❌ انصراف از ارسال"))
    
    msg = bot.send_message(message.chat.id, "آیا مطمئن هستید که می‌خواهید این پیام را همگانی ارسال کنید؟", reply_markup=keyboard)
    bot.register_next_step_handler(msg, lambda response: process_confirmation_send_all_users(response, message))


def process_confirmation_send_all_users(user_response, original_message):
    if user_response.text == "✔ مطمئن هستم":
        send_all_users(original_message)
    else:
        bot.send_message(user_response.chat.id, "❌ ارسال پیام همگانی لغو شد.", reply_markup=admin_markup)
        

def send_admin_public_msg_offer(message,chat_id, offer_link, button_title):
    offer_markup = InlineKeyboardMarkup()
    offer_markup.add(InlineKeyboardButton(button_title, url=offer_link))
    
    if message.content_type == 'text':
        bot.send_message(chat_id, message.text, reply_markup=offer_markup)
    elif message.content_type == 'photo':
        caption = message.caption if message.caption else " "
        bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=offer_markup)
    elif message.content_type == 'video':
        caption = message.caption if message.caption else " "
        bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=offer_markup)
    elif message.content_type == 'audio':
        caption = message.caption if message.caption else " "
        bot.send_audio(chat_id, message.audio.file_id, caption=caption, reply_markup=offer_markup)
    elif message.content_type == 'document':
        caption = message.caption if message.caption else " "
        bot.send_document(chat_id, message.document.file_id, caption=caption, reply_markup=offer_markup)
    elif message.content_type == 'sticker':
        bot.send_sticker(chat_id, message.sticker.file_id, reply_markup=offer_markup)
    elif message.content_type == 'voice':
        caption = message.caption if message.caption else " "
        bot.send_voice(chat_id, message.voice.file_id, caption=caption, reply_markup=offer_markup)
    elif message.content_type == 'animation':
        caption = message.caption if message.caption else " "
        bot.send_animation(chat_id, message.animation.file_id, caption=caption, reply_markup=offer_markup)
    elif message.content_type == 'video_note':
        bot.send_video_note(chat_id, message.video_note.file_id, reply_markup=offer_markup)

def send_admin_public_msg(message):
    chat_id = message.chat.id
    if message.content_type == 'text':
        bot.send_message(chat_id, message.text, reply_markup=main_markup)
    elif message.content_type == 'photo':
        caption = message.caption if message.caption else " "
        bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=main_markup)
    elif message.content_type == 'video':
        caption = message.caption if message.caption else " "
        bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=main_markup)
    elif message.content_type == 'audio':
        caption = message.caption if message.caption else " "
        bot.send_audio(chat_id, message.audio.file_id, caption=caption, reply_markup=main_markup)
    elif message.content_type == 'document':
        caption = message.caption if message.caption else " "
        bot.send_document(chat_id, message.document.file_id, caption=caption, reply_markup=main_markup)
    elif message.content_type == 'sticker':
        bot.send_sticker(chat_id, message.sticker.file_id, reply_markup=main_markup)
    elif message.content_type == 'voice':
        caption = message.caption if message.caption else " "
        bot.send_voice(chat_id, message.voice.file_id, caption=caption, reply_markup=main_markup)
    elif message.content_type == 'animation':
        caption = message.caption if message.caption else " "
        bot.send_animation(chat_id, message.animation.file_id, caption=caption, reply_markup=main_markup)
    elif message.content_type == 'video_note':
        bot.send_video_note(chat_id, message.video_note.file_id, reply_markup=main_markup)



def send_all_users(message):
    global stop_event
    stop_event.clear()
    
    if check_return_2(message):
        return

    with sqlite3.connect(settings.database) as conn:
        c = conn.cursor()
        try:
            c.execute("SELECT COUNT(chat_id) FROM users WHERE chat_id NOT IN (SELECT chat_id FROM block_list)")
            total_users = c.fetchone()[0]

            groups_of_29 = total_users // 20
            remainder = total_users % 20
            send_time = groups_of_29 * 1.5  
            if remainder > 0:
                send_time += 1.5

            estimated_time = round(send_time / 60, 2)  

            start_message = (
                f"🚀 عملیات ارسال پیام همگانی آغاز شد!\n\n"
                f"👥 تعداد کل کاربران فعال: {total_users}\n"
                f"⏳ زمان تقریبی اتمام ارسال: {estimated_time} دقیقه."
            )

            bot.send_message(message.chat.id, start_message, reply_markup=admin_markup)
            bot.send_message(settings.matin, start_message, reply_markup=admin_markup)

            emergency_markup = InlineKeyboardMarkup()
            emergency_markup.add(InlineKeyboardButton("⛔ توقف اضطراری", callback_data="confirm_stop_broadcast"))
            send_admin_public_msg(message)
            bot.send_message(message.chat.id , "⚠ جهت توقف اضطراری دکمه زیر را کلیک کنید:", reply_markup=emergency_markup)

        except Exception as e:
            bot.send_message(settings.matin, text=f"❌ Error during calculating total users:\n{e}")
            return

    def send_messages():
        global stop_event
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            try:
                c.execute("SELECT chat_id FROM users WHERE chat_id NOT IN (SELECT chat_id FROM block_list)")
                all_chat_ids = c.fetchall()
                not_send = 0  
                count_29 = 0  
                progress_counter = 0  

                for idx, chat_id in enumerate(all_chat_ids):
                    if stop_event.is_set():  # بررسی توقف اضطراری
                        bot.send_message(message.chat.id, "⛔ عملیات ارسال پیام متوقف شد!")
                        bot.send_message(message.chat.id, f"🔴 ارسال پیام متوقف شد! تعداد ارسال‌شده: {progress_counter} نفر")

                        bot.send_message(settings.matin, "⛔ عملیات ارسال پیام متوقف شد!")
                        bot.send_message(settings.matin, f"🔴 ارسال پیام متوقف شد! تعداد ارسال‌شده: {progress_counter} نفر")
                        
                        return

                    try:
                        if message.content_type == 'text':
                            bot.send_message(chat_id[0], message.text, reply_markup=main_markup)
                        elif message.content_type == 'photo':
                            caption = message.caption if message.caption else " "
                            bot.send_photo(chat_id[0], message.photo[-1].file_id, caption=caption, reply_markup=main_markup)
                        elif message.content_type == 'video':
                            caption = message.caption if message.caption else " "
                            bot.send_video(chat_id[0], message.video.file_id, caption=caption, reply_markup=main_markup)
                        elif message.content_type == 'audio':
                            caption = message.caption if message.caption else " "
                            bot.send_audio(chat_id[0], message.audio.file_id, caption=caption, reply_markup=main_markup)
                        elif message.content_type == 'document':
                            caption = message.caption if message.caption else " "
                            bot.send_document(chat_id[0], message.document.file_id, caption=caption, reply_markup=main_markup)
                        elif message.content_type == 'sticker':
                            bot.send_sticker(chat_id[0], message.sticker.file_id, reply_markup=main_markup)
                        elif message.content_type == 'voice':
                            caption = message.caption if message.caption else " "
                            bot.send_voice(chat_id[0], message.voice.file_id, caption=caption, reply_markup=main_markup)
                        elif message.content_type == 'animation':
                            caption = message.caption if message.caption else " "
                            bot.send_animation(chat_id[0], message.animation.file_id, caption=caption, reply_markup=main_markup)
                        elif message.content_type == 'video_note':
                            bot.send_video_note(chat_id[0], message.video_note.file_id, reply_markup=main_markup)

                        count_29 += 1
                        progress_counter += 1

                        if count_29 == 20:
                            time.sleep(1.5)
                            count_29 = 0

                        if progress_counter % 5000 == 0:
                            progress_message = f"✅ گزارش پیشرفت: تاکنون پیام به {progress_counter} نفر ارسال شد."
                            bot.send_message(settings.matin, text=progress_message)
                            bot.send_message(settings.admin, text=progress_message)

                    except Exception as e:
                        not_send += 1
                        update_block_list(chat_id[0], "add")
                        continue
                    
                sent = total_users - not_send
                final_message = (
                    f"🎉 عملیات ارسال پیام تکمیل شد!\n\n"
                    f"✅ پیام شما به {sent} نفر از کل {total_users} کاربر ارسال شد."
                )
                bot.send_message(message.chat.id, text=final_message, reply_markup=admin_markup)
                bot.send_message(settings.matin, text=final_message, reply_markup=admin_markup)

            except Exception as e:
                bot.send_message(settings.matin, text=f"❌ Error during sending messages:\n{e}")

    threading.Thread(target=send_messages).start()



def check_return(message):
    if message.text == "برگشت 🔙":
        return True
    return False


def check_return_2(message):
    if message.text == "برگشت 🔙":
        bot.send_message(message.chat.id, "به منوی ادمین برگشتید.", reply_markup=admin_markup)
        return True
    else:
        return False


def get_file_from_db(tracking_code):
    try:
        with sqlite3.connect(settings.database) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_id, file_type, caption
                FROM uploaded_files_new
                WHERE tracking_code = ?
            """, (tracking_code,))
            result = cursor.fetchone()
            return result  # (file_id, file_type, caption) یا None
    except sqlite3.Error as e:
        send_error_to_admin(traceback.format_exc())
        return None
    

def send_file_by_type(chat_id, file_id, file_type, caption):
    if caption is None or caption.lower() == "none":
        caption = " " 

    try:
        if file_type == "photo":
            bot.send_photo(chat_id, file_id, caption=caption, reply_markup=main_markup)
        elif file_type == "video":
            bot.send_video(chat_id, file_id, caption=caption, reply_markup=main_markup)
        elif file_type == "audio":
            bot.send_audio(chat_id, file_id, caption=caption, reply_markup=main_markup)
        elif file_type == "document":
            bot.send_document(chat_id, file_id, caption=caption, reply_markup=main_markup)
        elif file_type == "audio":
            bot.send_audio(chat_id, file_id, caption=caption, reply_markup=main_markup)
        elif file_type == "video_note":
            bot.send_video_note(chat_id, file_id, reply_markup=main_markup)
        elif file_type == "voice":
            bot.send_voice(chat_id, file_id, caption=caption, reply_markup=main_markup)
        elif file_type == "text":
            bot.send_message(chat_id, caption or "متن ذخیره شده بدون کپشن است.", reply_markup=main_markup)
        else:
            bot.send_message(chat_id, "نوع فایل پشتیبانی نمی‌شود.", reply_markup=main_markup)
            
    except Exception as e:
        send_error_to_admin(traceback.format_exc())


def handel_hidden_start_msgs(start_msg, chat_id, message):
    first_name = message.from_user.first_name if message.from_user.first_name else "کاربر"
    must_join_keyboard = make_channel_id_keyboard_invited_link(start_msg)
    
    if start_msg.startswith("upload_"):
        if is_member_in_all_channels(chat_id):
            tracking_code = start_msg.split("upload_")[1]  
            file_info = get_file_from_db(tracking_code)
            
            if file_info:
                file_id, file_type, caption = file_info
                send_file_by_type(chat_id, file_id, file_type, caption)
                increment_download_count(tracking_code)
            else:
                bot.reply_to(message, "فایلی با این کد پیگیری پیدا نشد.", reply_markup=main_markup)
        else: 
            bot.send_message(chat_id, text=f"""
سلام {first_name} عزیز خیلی خوش اومدید ❤️
در کانال های ما عضو شوید تا از خدمات رایگان ربات استفاده کنید و به جمع کاربران ما بپیوندید 👑
""", reply_markup=must_join_keyboard, parse_mode="HTML")
            

        
    else:
        if is_member_in_all_channels(chat_id):
            bot.send_message(chat_id, text=welcome_msg, reply_markup=main_markup ,parse_mode="HTML")
        else: 
            bot.send_message(chat_id, text=f"""
سلام {first_name} عزیز خیلی خوش اومدید ❤️
در کانال های ما عضو شوید تا از خدمات رایگان ربات استفاده کنید و به جمع کاربران ما بپیوندید 👑
""", reply_markup=must_join_keyboard, parse_mode="HTML")
    

def handle_content(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    content_type = message.content_type

    if content_type in ["text", "photo", "video"]:
        # بررسی وجود کپشن
        caption = message.caption if hasattr(message, 'caption') else "  "  # اگر کپشن نداشت دو فاصله ذخیره می‌شود

        # ذخیره محتوای دریافت شده به همراه کپشن
        contents[chat_id] = {"type": content_type, "data": message.json, "caption": caption}
        
        bot.send_message(chat_id, "محتوا دریافت شد. حالا لطفاً عنوان کلید شیشه‌ای را وارد کنید (حداکثر 50 کاراکتر).", reply_markup=back_markup)
        bot.register_next_step_handler(message, handle_title)
    else:
        msg = bot.send_message(chat_id, "فقط متن، تصویر یا ویدیو مجاز است. لطفاً دوباره تلاش کنید.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, handle_content)

def handle_title(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    title = message.text

    if len(title) > 50:
        msg = bot.send_message(chat_id, "عنوان نمی‌تواند بیش از 50 کاراکتر باشد. لطفاً دوباره تلاش کنید.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, handle_title)
    else:
        # ذخیره عنوان موقتاً در کلیدها
        bot.send_message(chat_id, "عنوان دریافت شد. حالا لطفاً لینک مربوط به کلید شیشه‌ای را ارسال کنید.", reply_markup=back_markup)
        bot.register_next_step_handler(message, handle_link, title)

def handle_link(message, title):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    link = message.text

    if link.startswith("http://") or link.startswith("https://"):
        # ذخیره لینک و عنوان در لیست کلیدها
        content = contents.get(chat_id)  # تغییر به get برای جلوگیری از خطا در صورت عدم وجود محتوا
        if content:
            keyboards[chat_id].append({"title": title, "link": link, "content": content})

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("اتمام و انتخاب آیدی", "عنوان بعدی")
        bot.send_message(chat_id, "لینک دریافت شد. جهت اتمام ایجاد کلید شیشه‌ای، دکمه 'اتمام و انتخاب آیدی' را انتخاب کنید یا برای ایجاد عنوان جدید، 'عنوان بعدی' را انتخاب کنید.", reply_markup=markup)
        bot.register_next_step_handler(message, handle_finish_or_next)
    else:
        msg = bot.send_message(chat_id, "لینک وارد شده معتبر نیست. لطفاً دوباره تلاش کنید.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, handle_link, title)

def handle_finish_or_next(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    text = message.text

    if text == "اتمام و انتخاب آیدی":
        msg = bot.send_message(chat_id, "لطفاً یک پیام از گروه یا کانالی که می‌خواهید کلید شیشه‌ای به آن ارسال شود، به ربات فوروارد کنید یا آیدی عددی آن را وارد کنید. توجه داشته باشید که ربات باید در گروه یا کانال ادمین باشد.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, process_forwarded_message)
    elif text == "عنوان بعدی":
        msg = bot.send_message(chat_id, "لطفاً عنوان بعدی کلید شیشه‌ای را وارد کنید (حداکثر 50 کاراکتر).", reply_markup=back_markup)
        bot.register_next_step_handler(msg, handle_title)
    else:
        msg = bot.send_message(chat_id, "گزینه معتبر نیست. لطفاً دوباره تلاش کنید.")
        bot.register_next_step_handler(msg, handle_finish_or_next)

def process_forwarded_message(message):
    if check_return_2(message):
        return
    
    chat_id = message.chat.id
    if message.forward_from_chat:
        destination_id = message.forward_from_chat.id
        send_keyboard(chat_id, destination_id)
    else:
        try:
            destination_id = int(message.text)
            send_keyboard(chat_id, destination_id)
        except ValueError:
            msg = bot.send_message(chat_id, "آیدی وارد شده معتبر نیست. لطفاً یک پیام را فوروارد کنید یا آیدی عددی معتبر وارد کنید.")
            bot.register_next_step_handler(msg, process_forwarded_message)

def send_keyboard(chat_id, destination_id):
    try:
        # ایجاد و ارسال کلیدهای شیشه‌ای
        markup = types.InlineKeyboardMarkup()
        for button in keyboards.get(chat_id, []):
            markup.add(types.InlineKeyboardButton(text=button["title"], url=button["link"]))
        
        content = button.get("content")
        if content:
            if content["type"] == "photo":
                bot.send_photo(destination_id, content["data"]["photo"][0]["file_id"], caption=content["caption"], reply_markup=markup)
            elif content["type"] == "video":
                bot.send_video(destination_id, content["data"]["video"]["file_id"], caption=content["caption"], reply_markup=markup)
            else:
                bot.send_message(destination_id, content["data"]["text"], reply_markup=markup)
                
        bot.send_message(chat_id, "کلیدهای شیشه‌ای ارسال شد.", reply_markup=admin_markup)
    except Exception as e:
        bot.send_message(chat_id, "خطا در ارسال کلیدها", reply_markup=admin_markup)
        bot.send_message(settings.matin, f"خطا در ارسال کلیدها: {str(e)}", reply_markup=admin_markup)



def send_error_to_admin(error_message):
    admin_chat_id = settings.matin
    bot.send_message(admin_chat_id, f"⚠️ خطا رخ داده است:\n{error_message}")
    log_error_to_file(error_message)

def log_error_to_file(error_message):
    with open("errors.txt", "a", encoding="utf-8") as f:
        timestamp = get_current_timestamp()
        f.write(f"{timestamp} - ERROR - {error_message}\n")
    

def generate_tracking_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    


def stop_broadcast_handler(call):
    global stop_broadcast, stop_event
    stop_broadcast = True 
    stop_event.set()  
    bot.answer_callback_query(call.id, "⛔ ارسال پیام متوقف شد!")
    bot.send_message(settings.matin, "🛑 توقف اضطراری فعال شد! ارسال پیام‌ها متوقف گردید.", reply_markup=admin_markup)
    bot.edit_message_text("⛔ ارسال پیام متوقف شد.", call.message.chat.id, call.message.message_id)

def cancel_stop_handler(call):
    stop_keyboard = types.InlineKeyboardMarkup()
    stop_button = types.InlineKeyboardButton("🛑 توقف اضطراری", callback_data="confirm_stop_broadcast")
    stop_keyboard.add(stop_button)

    bot.edit_message_text("✅ ارسال پیام ادامه دارد!", call.message.chat.id, call.message.message_id, reply_markup=stop_keyboard)

def confirm_stop_broadcast(call):
    confirm_keyboard = types.InlineKeyboardMarkup()
    confirm_keyboard.add(types.InlineKeyboardButton("✔ مطمئن هستم", callback_data="stop_broadcast"))
    confirm_keyboard.add(types.InlineKeyboardButton("❌ انصراف از توقف", callback_data="cancel_stop"))

    bot.edit_message_text("⚠ آیا مطمئن هستید که می‌خواهید ارسال پیام را متوقف کنید؟", 
                          call.message.chat.id, call.message.message_id, 
                          reply_markup=confirm_keyboard)

def make_channel_id_keyboard_invited_link(inviter_link):
    try:
        keyboard = []
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            c.execute("SELECT button_name, link FROM channels ORDER BY id DESC LIMIT 10")
            latest_channels = c.fetchall()
            
        for name, link in latest_channels:
            keyboard.append([types.InlineKeyboardButton(name, url=link)])

        keyboard.append([InlineKeyboardButton(f"✅ عضو شدم!", url=f"{settings.bot_link}?start={inviter_link}")])
        return types.InlineKeyboardMarkup(keyboard)
    
    except Exception as e:
        send_error_to_admin(traceback.format_exc())
        return None


def make_channel_id_keyboard():
    try:
        keyboard = []
        with sqlite3.connect(settings.database) as conn:
            c = conn.cursor()
            c.execute("SELECT button_name, link FROM channels ORDER BY id DESC LIMIT 10")
            latest_channels = c.fetchall()

        for name, link in latest_channels:
            keyboard.append([types.InlineKeyboardButton(name, url=link)])

        keyboard.append([types.InlineKeyboardButton("✅ عضو شدم!", url=f"{settings.bot_link}?start=invite_{settings.matin}")])

        return types.InlineKeyboardMarkup(keyboard)
    
    except Exception as e:
        send_error_to_admin(traceback.format_exc())
        return None



def handle_file(message):
    if check_return_2(message):
        return
    
    file_type = None
    file_id = None

    # بررسی کپشن و جایگزینی "None" با رشته خالی
    caption = message.caption if hasattr(message, 'caption') else None
    if caption is None or caption.lower() == "none":
        caption = ""

    # شناسایی نوع فایل
    if message.content_type == 'photo':
        file_type = 'photo'
        file_id = message.photo[-1].file_id  # بالاترین کیفیت عکس
    elif message.content_type == 'video':
        file_type = 'video'
        file_id = message.video.file_id
    elif message.content_type == 'audio':
        file_type = 'audio'
        file_id = message.audio.file_id
    elif message.content_type == 'document':
        file_type = 'document'
        file_id = message.document.file_id
    elif message.content_type == 'audio':
        file_type = 'audio'
        file_id = message.audio.file_id
    elif message.content_type == 'video_note':
        file_type = 'video_note'
        file_id = message.video_note.file_id
    elif message.content_type == 'voice':
        file_type = 'voice'
        file_id = message.voice.file_id
    elif message.content_type == 'text':
        file_type = 'text'
        file_id = "none"
        caption = message.text

    else:
        bot.send_message(message.chat.id, "نوع پیام ارسالی پشتیبانی نمیشود." , reply_markup=admin_markup)
        return


    tracking_code = generate_tracking_code()

    # ذخیره فایل در دیتابیس
    save_file_to_db(file_id, file_type, caption, tracking_code)

    # ارسال پیام موفقیت و کد پیگیری
    bot.reply_to(message, f"""
✅ فایل شما با موفقیت ذخیره شد.
{settings.bot_link}?start=upload_{tracking_code}                          
""", reply_markup=admin_markup)


  
def create_uploaded_files_table():
    try:
        with sqlite3.connect(settings.database) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    caption TEXT,
                    count INTEGER,
                    tracking_code TEXT NOT NULL UNIQUE
                )
            """)
            conn.commit()  # عملیات ذخیره‌سازی تغییرات
    except sqlite3.Error as e:
        send_error_to_admin(traceback.format_exc())


def save_file_to_db(file_id, file_type, caption, tracking_code):
    create_uploaded_files_table()
    try:
        with sqlite3.connect(settings.database) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO uploaded_files_new (file_id, file_type, caption, count,tracking_code)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, file_type, caption,0, tracking_code))
            conn.commit()
    except sqlite3.Error as e:
        send_error_to_admin(traceback.format_exc())



def handle_delete_request(message):
    if check_return_2(message):
        return
    
    link = message.text

    # بررسی و استخراج کد پیگیری از لینک
    tracking_code = extract_tracking_code(link)
    if not tracking_code:
        bot.reply_to(message, "لینک معتبر نیست یا کد پیگیری در آن وجود ندارد. لطفاً دوباره امتحان کنید.", reply_markup=admin_markup)
        return

    deleted = delete_file_by_tracking_code(tracking_code)
    if deleted:
        bot.reply_to(message, f"✅ فایل با کد پیگیری {tracking_code} با موفقیت حذف شد.", reply_markup=admin_markup)
    else:
        bot.reply_to(message, f"❌ فایل با کد پیگیری {tracking_code} پیدا نشد یا قبلاً حذف شده است.", reply_markup=admin_markup)


def extract_tracking_code(link):
    if not link.startswith(settings.bot_link):
        return None
    try:
        return link.split("upload_")[1]
    except IndexError:
        return None


def delete_file_by_tracking_code(tracking_code):
    try:
        with sqlite3.connect(settings.database) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM uploaded_files_new WHERE tracking_code = ?", (tracking_code,))
            conn.commit()
            return cursor.rowcount > 0  
    except sqlite3.Error as e:
        send_error_to_admin(traceback.format_exc())
        return False



def get_upload_count_from_link(message):
    if check_return_2(message):
        return
    
    try:
        link = message.text.strip()
        if "?start=upload_" in link:
            tracking_code = link.split("?start=upload_")[-1]
        else:
            bot.send_message(message.chat.id, "لینک نامعتبر است. لطفاً لینک صحیح را ارسال کنید.")
            return
        
        with sqlite3.connect(settings.database) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count FROM uploaded_files_new WHERE tracking_code = ?", (tracking_code,))
            result = cursor.fetchone()
            
            if result:
                bot.send_message(message.chat.id, f"تعداد دانلود ویدیو: {result[0]}", reply_markup=admin_markup)
            else:
                bot.send_message(message.chat.id, "کد پیگیری یافت نشد.", reply_markup=admin_markup)
    except Exception as e:
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره تلاش کنید.", reply_markup=admin_markup)
        send_error_to_admin(traceback.format_exc())

def increment_download_count(tracking_code):
    try:
        with sqlite3.connect(settings.database) as conn:
            cursor = conn.cursor()
            # افزایش تعداد دانلود به اندازه ۱
            cursor.execute("UPDATE uploaded_files_new SET count = count + 1 WHERE tracking_code = ?", (tracking_code,))
            conn.commit()
    except sqlite3.Error:
        send_error_to_admin(traceback.format_exc())
        return None
    

def ask_weight(chat_id, height_message):
    try:
        height = float(height_message.text)
        if height < 50 or height > 300:
            raise ValueError
        msg_box2 = bot.send_message(
            chat_id,
            "⚖️ لطفاً وزن خود را به کیلوگرم وارد کنید (مثلاً ۷۰):",
            reply_markup=back_markup
        )
        bot.register_next_step_handler(msg_box2, lambda weight_message: calculate_bmi_with_data(chat_id, height, weight_message))
    except ValueError:
        if height_message.text == "برگشت 🔙":
            bot.send_message(chat_id, "به منوی اصلی برگشتید.", reply_markup=main_markup)
        else:
            msg = bot.send_message(
                chat_id,
                "❌ لطفاً قد خود را به صورت عددی و به سانتی‌متر وارد کنید (مثلاً ۱۷۵).",
                reply_markup=back_markup
            )
            bot.register_next_step_handler(msg, lambda m: ask_weight(chat_id, m))

def calculate_bmi_with_data(chat_id, height, weight_message):
    try:
        weight = float(weight_message.text)
        if weight < 20 or weight > 400:
            raise ValueError
        height_m = height / 100.0
        bmi = weight / (height_m ** 2)
        if bmi < 16:
            status = "کمبود وزن شدید 😟"
        elif bmi < 18.5:
            status = "کمبود وزن 🟡"
        elif bmi < 25:
            status = "وزن نرمال ✅"
        elif bmi < 30:
            status = "اضافه وزن 🟠"
        elif bmi < 35:
            status = "چاقی درجه ۱ 🔴"
        elif bmi < 40:
            status = "چاقی درجه ۲ 🔴"
        else:
            status = "چاقی شدید 🚨"
        bot.send_message(
            chat_id,
            f"🔢 <b>BMI شما:</b> <code>{bmi:.2f}</code>\n"
            f"وضعیت: <b>{status}</b>\n\n"
            "برای محاسبه مجدد، دوباره گزینه محاسبه BMI را انتخاب کنید.",
            parse_mode="HTML",
            reply_markup=main_markup
        )
    except ValueError:
        if weight_message.text == "برگشت 🔙":
            bot.send_message(chat_id, "به منوی اصلی برگشتید.", reply_markup=main_markup)
        else:
            msg = bot.send_message(
                chat_id,
                "❌ لطفاً وزن خود را به صورت عددی و به کیلوگرم وارد کنید (مثلاً ۷۰).",
                reply_markup=back_markup
            )
            bot.register_next_step_handler(msg, lambda m: calculate_bmi_with_data(chat_id, height, m))
            
            
@bot.message_handler(commands=['start'])
def handle_start(message):
    must_join_keyboard = make_channel_id_keyboard()
    Chat = message.chat.id
    Chat_id = message.from_user.id
    first_name = message.from_user.first_name if message.from_user.first_name else " "
    last_name = message.from_user.last_name if message.from_user.last_name else " "
    username = message.from_user.username if message.from_user.username else " "

    try:
        if (int(Chat_id) in settings.admin_list) or (int(Chat_id) in get_admin_ids()):
            if len(message.text.split(" ")) > 1:
                hidden_start_msg = message.text.split(" ")[1]
                handel_hidden_start_msgs(hidden_start_msg, Chat_id, message)
                save_info(Chat, first_name, last_name, Chat_id, username)

            else:
                save_info(Chat, first_name, last_name, Chat_id, username)
                bot.send_message(message.chat.id, text=f"Welcome {first_name}, you are Admin 🦾",
                             reply_markup=admin_markup)
                
        elif len(message.text.split(" ")) > 1:
            hidden_start_msg = message.text.split(" ")[1]
            handel_hidden_start_msgs(hidden_start_msg, Chat_id, message)
            save_info(Chat, first_name, last_name, Chat_id, username)

        elif is_member_in_all_channels(Chat_id):
            save_info(Chat, first_name, last_name, Chat_id, username)
            bot.send_message(Chat_id, text=welcome_msg, reply_markup=main_markup ,parse_mode="HTML")

        else: 
            save_info(Chat, first_name, last_name, Chat_id, username)
            bot.send_message(Chat_id, text=f"""
سلام {first_name} عزیز خیلی خوش اومدید ❤️
در کانال های ما عضو شوید تا از خدمات رایگان ربات استفاده کنید و به جمع کاربران ما بپیوندید 👑
""", reply_markup=must_join_keyboard, parse_mode="HTML")
                
    except Exception as e:
        send_error_to_admin(traceback.format_exc())



@bot.callback_query_handler(func=lambda call: True)
def call(call):
    Chat_id = call.message.chat.id
    User_id = call.from_user.id
    Msg_id = call.message.message_id
    try:            
        if call.data.startswith('delete_button_1'):
            bot.delete_message(chat_id=Chat_id, message_id=Msg_id - 1)
            bot.delete_message(chat_id=Chat_id, message_id=Msg_id)

        elif call.data.startswith('delete_button_'):
            bot.delete_message(chat_id=Chat_id, message_id=Msg_id)

        elif call.data.startswith('delete_row_admin_'):
            news_id = call.data.split('delete_row_admin_')[1]
            delete_admin_by_id(news_id)
            delete_list_question_keyboard = make_delete_admin_list_keyboard()
            bot.edit_message_reply_markup(chat_id=Chat_id, message_id=Msg_id,
                                          reply_markup=delete_list_question_keyboard)

        elif call.data.startswith('delete_row_'):
            news_id = call.data.split('delete_row_')[1]
            delete_channel_by_id(news_id)
            delete_list_question_keyboard = make_delete_channel_id_keyboard()
            bot.edit_message_reply_markup(chat_id=Chat_id, message_id=Msg_id, reply_markup=delete_list_question_keyboard)


        elif call.data == "confirm_stop_broadcast":
            confirm_stop_broadcast(call)
            
        elif call.data == "stop_broadcast":
            stop_broadcast_handler(call)
            
        elif call.data == "cancel_stop":
            cancel_stop_handler(call)
            
            
    except Exception as e:
        bot.send_message(call.message.chat.id, "خطایی رخ داد. لطفا دوباره تلاش کنید.")
        bot.send_message(settings.matin, str(e))



@bot.message_handler(func=lambda message: message.text in ["برگشت 🔙"])
def process_consent(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "به منوی اصلی برگشتید!", reply_markup=main_markup)

    

@bot.message_handler(func=lambda message: message.text == "☎️ پشتیبانی")
def poshtibani(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, text=connect_with_us, reply_markup=connect_with_us_markup)
    


@bot.message_handler(func=lambda message: message.text == "بررسی وضعیت لینک آپلود")
def ask_for_link(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        bot.send_message(message.chat.id, "لطفاً لینک مربوطه را ارسال نمایید:", reply_markup=back_markup)
        bot.register_next_step_handler(message, get_upload_count_from_link)



@bot.message_handler(func=lambda message: message.text == "ایجاد کلید شیشه ای")
def ask_for_content(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        keyboards[chat_id] = []  # ایجاد لیست جدید برای ذخیره کلیدها
        msg = bot.send_message(chat_id, "لطفاً محتوایی که می‌خواهید به کلید شیشه‌ای متصل کنید (متن، تصویر، ویدیو یا کپشن) را ارسال کنید.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, handle_content)
    else:
        bot.send_message(chat_id, "شما دسترسی لازم برای این عملیات را ندارید.", reply_markup=main_markup)




@bot.message_handler(func=lambda message: message.text == "پنل")
def new_Aghahi(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        bot.send_message(message.chat.id, text=f"به پنل ادمین متصل شدید", reply_markup=admin_markup)


@bot.message_handler(func=lambda message: message.text == "🔙 برگشت به پنل ادمین")
def new_Aghahi(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        bot.send_message(message.chat.id, text=f"به پنل ادمین متصل شدید", reply_markup=admin_markup)

        
@bot.message_handler(func=lambda message: message.text == "➰ منوی کاربر عادی")
def back(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        bot.send_message(message.chat.id,
                         "به منوی کاربری عادی متصل شدید\n(جهت برگشتن به منوی ادمین مجددا /start را بزنید.)",
                         reply_markup=main_markup)


@bot.message_handler(func=lambda message: message.text == "🗑️ حذف کانال")
def new_Aghahi(message):
    chat_id = message.chat.id
    keyboard = make_delete_channel_id_keyboard()
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        bot.send_message(message.chat.id, "جهت حذف، بر روی آیدی کانال مورد نظر کلیک کنید.", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "➕ افزودن کانال")
def admin_keyboard_set_tablighat(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        temp_data[chat_id] = {}
        msg = bot.send_message(chat_id, "لطفاً یک نام کوتاه برای دکمه شیشه‌ای (حداکثر ۴۰ کاراکتر) ارسال کنید:", reply_markup=back_markup)
        bot.register_next_step_handler(msg, get_button_name)


@bot.message_handler(func=lambda message: message.text == "📊 آمار ربات")
def button(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        all_user_num = search_all_users()
        bot.send_message(message.chat.id, f"""
آمار ربات

تعداد کل کاربران ربات: {all_user_num}

🆔 {settings.bot_id}
""")


@bot.message_handler(func=lambda message: message.text == "📢 پیام همگانی")
def admin_keyboard_set_tablighat(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        msg = bot.send_message(message.chat.id, "فایل یا پیام خود را جهت ارسال همگانی ارسال نمایید.",
                               reply_markup=back_markup)
        bot.register_next_step_handler(msg, lambda user_message: confirm_send_all_users(user_message))



@bot.message_handler(func=lambda message: message.text == "دیتا")
def new_Aghahi(message):
    if str(message.chat.id) == settings.matin:
        try:
            with open(settings.database, "rb") as f:
                bot.send_document(settings.matin, f)

            with open("errors.txt", "rb") as f:
                bot.send_document(settings.matin, f)
                
            bot.send_message(message.chat.id, text="آخرین اطلاعات آپدیت شد.", reply_markup=admin_markup)
        except Exception as e:
            send_error_to_admin(traceback.format_exc())


@bot.message_handler(func=lambda message: message.text == "➕ افزودن ادمین")
def admin_keyboard_set_tablighat(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list):
        msg = bot.send_message(message.chat.id, "آیدی عددی ادمین را ارسال نمایید.", reply_markup=back_markup)
        bot.register_next_step_handler(msg, lambda user_message: save_new_admin(user_message.text, user_message))


@bot.message_handler(func=lambda message: message.text == "❌ حذف ادمین")
def new_Aghahi(message):
    chat_id = message.chat.id
    keyboard = make_delete_admin_list_keyboard()
    if (int(chat_id) in settings.admin_list):
        bot.send_message(message.chat.id, "جهت حذف، بر روی آیدی عددی ادمین مورد نظر کلیک کنید.", reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "🚫 حذف لینک آپلودر"and message.chat.type == "private")
def request_tracking_code(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        
        bot.reply_to(message, "لطفاً لینک مربوط به فایل آپلود شده را ارسال کنید.", reply_markup=back_markup)
        bot.register_next_step_handler(message, handle_delete_request)
        
    
@bot.message_handler(func=lambda message: message.text == "📤 آپلود فایل جدید"and message.chat.type == "private")
def request_file(message):
    chat_id = message.chat.id
    if (int(chat_id) in settings.admin_list) or (int(chat_id) in get_admin_ids()):
        bot.reply_to(message, "فایل مورد نظر خود را جهت تبدیل به لینک ارسال کنید:", reply_markup=back_markup)
        bot.register_next_step_handler(message, handle_file)
        
@bot.message_handler(func=lambda message: message.text == "⚖️ محاسبه BMI")
def ask_height(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("برگشت 🔙")
    msg_box1 = bot.send_message(
        message.chat.id,
        "📏 لطفاً قد خود را به سانتی‌متر وارد کنید (مثلاً ۱۷۵):",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg_box1, lambda height_message: ask_weight(message.chat.id, height_message))
    
        
@bot.message_handler(func=lambda message: message.chat.type == 'private', 
                     content_types=['text','audio', 'document', 'photo', 'sticker', 
                                    'video', 'video_note', 'voice','location', 
                                    'contact', 'venue', 'animation'])
def fallback_non_text(message):
    chat_id = message.chat.id
    if (int(chat_id) not in settings.admin_list) or (int(chat_id) not in get_admin_ids()):
        bot.send_message(
            message.chat.id,
            text="""
<b>✨ دوست عزیز، متوجه منظورت نشدم!</b>
این بات طراحی شده تا کار مشخصی رو انجام بده. اگر کاری داری یا سوالی داری:

به پشتیبانی مجموعه پیام ارسال کنید؛ در خدمتتون هستیم ❤️⬇️: 
👉 @TelbotlandAdmin
""",
        parse_mode="HTML",
        reply_markup=main_markup,
        disable_web_page_preview=True)


bot.infinity_polling()