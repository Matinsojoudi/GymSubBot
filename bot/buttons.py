from telebot.types import ReplyKeyboardMarkup
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from env import settings

back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
back_markup.row("برگشت 🔙")

admin_markup = ReplyKeyboardMarkup(resize_keyboard=True)
admin_markup.row("🗑️ حذف کانال", "➕ افزودن کانال")
admin_markup.row("🗑️ حذف ادمین", "➕ افزودن ادمین")
admin_markup.row("📢 پیام همگانی", "📊 آمار ربات")
admin_markup.row("➰ منوی کاربر عادی")

main_markup = ReplyKeyboardMarkup(resize_keyboard=True)
main_markup.row("خرید اشتراک باشگاه")
main_markup.row("پروفایل من", "درخواست برنامه تمرینی")
main_markup.row("مشاهده سوابق خرید من", "مشاهده برنامه تمرینی من")

main_markup.row("📞 ارتباط با پشتیبانی")

send_post_type_markup = ReplyKeyboardMarkup(resize_keyboard=True)
send_post_type_markup.row("شروع از آخرین پست" ,"شروع از اول")
send_post_type_markup.row("برگشت 🔙")

cheack_delete_markup = ReplyKeyboardMarkup(resize_keyboard=True)
cheack_delete_markup.row("❌ لغو عملیات پاکسازی" ,"✅ تایید عملیات پاکسازی")

connect_with_us_markup = InlineKeyboardMarkup()
connect_with_us_markup.add(InlineKeyboardButton("🛎️ پشتیبانی مجموعه", url="https://t.me/mrmahmoudi_support"))

