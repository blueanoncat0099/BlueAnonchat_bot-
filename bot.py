import os
import sqlite3
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

db = sqlite3.connect("messages.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS message_map (
    owner_message_id INTEGER PRIMARY KEY,
    user_chat_id INTEGER NOT NULL
)
""")
db.commit()


def save_message(owner_message_id, user_chat_id):
    db.execute(
        "INSERT OR REPLACE INTO message_map VALUES (?, ?)",
        (owner_message_id, user_chat_id),
    )
    db.commit()


def get_user_chat(owner_message_id):
    result = db.execute(
        "SELECT user_chat_id FROM message_map WHERE owner_message_id = ?",
        (owner_message_id,),
    ).fetchone()

    return result[0] if result else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text(
            "پنل مدیریت فعاله 💙\n\n"
            "هر وقت پیامی از یک کاربر ناشناس دریافت کردی، "
            "روی همان پیام Reply کن تا جواب برای خودش ارسال شود."
        )
        return

    await update.message.reply_text(
        "سلام 💙\n\n"
        "اینجا می‌تونی به صورت ناشناس پیام بفرستی.\n"
        "پیامت بدون اسم و یوزرنیمت برای صاحب بات ارسال میشه.\n\n"
        "برای پایان دادن به چت /stop رو بفرست."
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        return

    await update.message.reply_text(
        "چت ناشناس پایان یافت 💙"
    )


async def user_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    if update.effective_user.id == OWNER_ID:
        return

    try:
        sent = await context.bot.copy_message(
            chat_id=OWNER_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )

        save_message(
            sent.message_id,
            update.effective_chat.id
        )

        await update.message.reply_text(
            "پیامت به صورت ناشناس ارسال شد 💙"
        )

    except Exception as e:
        logging.exception(e)

        await update.message.reply_text(
            "متأسفانه ارسال پیام انجام نشد. دوباره امتحان کن."
        )


async def owner_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    if update.effective_user.id != OWNER_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "برای جواب دادن به یک کاربر، روی پیام همان کاربر Reply کن."
        )
        return

    owner_message_id = update.message.reply_to_message.message_id

    user_chat_id = get_user_chat(owner_message_id)

    if not user_chat_id:
        await update.message.reply_text(
            "این پیام دیگر در سیستم ثبت نشده یا مربوط به یک پیام قدیمی است."
        )
        return

    try:
        await context.bot.copy_message(
            chat_id=user_chat_id,
            from_chat_id=OWNER_ID,
            message_id=update.message.message_id,
        )

        await update.message.reply_text(
            "پاسخ ارسال شد 💙"
        )

    except Exception as e:
        logging.exception(e)

        await update.message.reply_text(
            "ارسال پاسخ انجام نشد. ممکنه کاربر چت رو بسته باشه."
        )


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    app.add_handler(
        MessageHandler(
            filters.ALL
            & ~filters.COMMAND
            & ~filters.User(user_id=OWNER_ID),
            user_message,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.ALL & filters.User(user_id=OWNER_ID),
            owner_message,
        )
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
