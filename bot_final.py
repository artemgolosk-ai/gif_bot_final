import telebot
import os
import subprocess
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8743228085:AAFcR0mQF43CVITanfW_6yloa4HxdmYfLDo"

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

user_settings = {}

def main_menu(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🎬 Фото → GIF", callback_data="photo"),
        InlineKeyboardButton("🎥 Видео → GIF", callback_data="video"),
        InlineKeyboardButton("⚙️ Качество", callback_data="quality")
    )
    bot.send_message(chat_id, "🎬 **Главное меню**\n\nВыбери действие:", parse_mode="Markdown", reply_markup=markup)

# ФОТО → GIF (через FFmpeg, чтобы Telegram распознал)
@bot.message_handler(content_types=['photo'])
def photo_to_gif(message):
    chat_id = message.chat.id
    settings = user_settings.get(chat_id, {"quality": "medium"})
    
    size = {"high": 1080, "medium": 400, "low": 144}[settings["quality"]]
    
    try:
        bot.reply_to(message, f"🎬 Делаю гифку... {size}px")
        
        # Скачиваем фото
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        with open("temp.jpg", "wb") as f:
            f.write(downloaded)
        
        # Конвертируем фото в гифку через FFmpeg (20 кадров = 2 секунды)
        cmd = [
            'ffmpeg', '-loop', '1', '-i', 'temp.jpg',
            '-vf', f'scale={size}:{size}:flags=lanczos,fps=10',
            '-t', '2',  # 2 секунды
            '-r', '10',  # 10 кадров в секунду
            '-f', 'gif',
            'out.gif',
            '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        if os.path.exists("out.gif") and os.path.getsize("out.gif") > 1000:
            # Отправляем как документ с правильным mime-типом
            with open("out.gif", "rb") as gif:
                bot.send_document(
                    chat_id,
                    gif,
                    caption="🎬 **Гифка готова!**\n\n⬇️ Нажми на файл, потом ⋮ в правом углу\n→ **'Сохранить в свои GIF'**",
                    visible_file_name="animation.gif",
                    parse_mode="Markdown"
                )
        else:
            bot.reply_to(message, "❌ Ошибка: файл слишком маленький")
        
        os.remove("temp.jpg")
        os.remove("out.gif")
        
    except Exception as e:
        bot.reply_to(message, f"❌ {e}")

# ВИДЕО → GIF
@bot.message_handler(content_types=['video', 'video_note'])
def video_to_gif(message):
    chat_id = message.chat.id
    settings = user_settings.get(chat_id, {"quality": "medium"})
    
    scale = {"high": 1080, "medium": 400, "low": 144}[settings["quality"]]
    
    try:
        bot.reply_to(message, f"🎬 Конвертирую видео... {scale}px")
        
        if message.video:
            file_id = message.video.file_id
        else:
            file_id = message.video_note.file_id
        
        file_info = bot.get_file(file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        with open("temp.mp4", "wb") as f:
            f.write(downloaded)
        
        # Конвертируем видео в гифку
        cmd = [
            'ffmpeg', '-i', 'temp.mp4',
            '-vf', f'fps=15,scale={scale}:-1:flags=lanczos',
            '-t', '8',
            '-f', 'gif',
            'out.gif',
            '-y'
        ]
        subprocess.run(cmd, capture_output=True)
        
        if os.path.exists("out.gif") and os.path.getsize("out.gif") > 1000:
            with open("out.gif", "rb") as gif:
                bot.send_document(
                    chat_id,
                    gif,
                    caption="🎬 **Гифка готова!**\n\n⬇️ Нажми на файл, потом ⋮ в правом углу\n→ **'Сохранить в свои GIF'**",
                    visible_file_name="animation.gif",
                    parse_mode="Markdown"
                )
            os.remove("temp.mp4")
            os.remove("out.gif")
        else:
            bot.reply_to(message, "❌ Не удалось создать GIF")
            
    except Exception as e:
        bot.reply_to(message, f"❌ {e}")

# КНОПКИ
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "photo":
        bot.edit_message_text("📸 Отправь **одно фото** — сделаю гифку 2 секунды!", chat_id, call.message.message_id, parse_mode="Markdown")
    
    elif call.data == "video":
        bot.edit_message_text("🎥 Отправь **видео** или **кружок** — сделаю гифку!", chat_id, call.message.message_id, parse_mode="Markdown")
    
    elif call.data == "quality":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔥 1080p", callback_data="set_high"),
            InlineKeyboardButton("⚡ 400p", callback_data="set_medium"),
            InlineKeyboardButton("🤡 144p", callback_data="set_low")
        )
        bot.edit_message_text("⚙️ **Выбери качество:**", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    
    elif call.data == "set_high":
        user_settings[chat_id] = {"quality": "high"}
        bot.answer_callback_query(call.id, "✅ 1080p")
        bot.edit_message_text("✅ Качество: **1080p**\n\nТеперь отправляй фото или видео!", chat_id, call.message.message_id, parse_mode="Markdown")
    
    elif call.data == "set_medium":
        user_settings[chat_id] = {"quality": "medium"}
        bot.answer_callback_query(call.id, "✅ 400p")
        bot.edit_message_text("✅ Качество: **400p**\n\nТеперь отправляй фото или видео!", chat_id, call.message.message_id, parse_mode="Markdown")
    
    elif call.data == "set_low":
        user_settings[chat_id] = {"quality": "low"}
        bot.answer_callback_query(call.id, "✅ 144p")
        bot.edit_message_text("✅ Качество: **144p**\n\nТеперь отправляй фото или видео!", chat_id, call.message.message_id, parse_mode="Markdown")

# КОМАНДЫ
@bot.message_handler(commands=['start', 'menu'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "🎬 **Привет! Я делаю гифки из фото и видео!**\n\nВыбери действие в меню 👇", parse_mode="Markdown")
    main_menu(chat_id)

@bot.message_handler(func=lambda m: True)
def text_handler(message):
    main_menu(message.chat.id)

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 БОТ ЗАПУЩЕН!")
    print("📸 Фото → GIF (2 секунды, FFmpeg)")
    print("🎥 Видео/кружок → GIF")
    print("💾 Telegram должен показать кнопку 'Сохранить в свои GIF'")
    print("=" * 50)
    bot.infinity_polling()
