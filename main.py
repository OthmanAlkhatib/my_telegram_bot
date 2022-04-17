from telegram.ext import CommandHandler, Updater, ConversationHandler, MessageHandler, Filters, CallbackContext
from telegram import (KeyboardButton, ReplyKeyboardMarkup, Update)
from dataSource import DataSource
import os
import threading
import time
import datetime
import logging
import sys


ADD_REMINDER_TEXT = "Add Remainder ⏰"
TIME_SLEEP = 20

# TOKEN = "5328781640:AAFOmH1jv53Xehl_oOMBK4LleHxYqTzBUPE"
TOKEN = os.getenv("TOKEN")
# DATABASE_URL = "postgres://othman_user:congratulation@localhost:5432/ahsan_alhadeeth_telegram"
DATABASE_URL = os.environ.get("DATABASE_URL")
ENTER_MESSAGE, ENTER_TIME = range(2)

data_source = DataSource(DATABASE_URL)

MODE = os.getenv("MODE")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

if MODE == "dev":
    def run():
        logger.info("Start in DEV mode")
        updater.start_polling()
elif MODE == "prod":
    def run():
        logger.info("Start in PROD mode")
        updater.start_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 5000)), url_path=TOKEN,
                              webhook_url="https://{}.herokuapp.com/{}".format("my-telegram-bottt", TOKEN))
        # updater.bot.setWebhook('https://my-telegram-bottt.herokuapp.com/' + TOKEN)
else:
    logger.error("No mode specified")
    sys.exit(1)

def start_handler(update, context):
    # Reply With Next Step (Buttons)
    update.message.reply_text("Hello, Creator!", reply_markup=add_reminder_button())


def add_reminder_button():
    # Storing Buttons (Rows and Columns)
    keyboard = [[KeyboardButton(ADD_REMINDER_TEXT)]]
    return ReplyKeyboardMarkup(keyboard)


def add_reminder_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Please enter a message of the reminder:")
    # What is Next Step
    return ENTER_MESSAGE


def enter_message_handler(update: Update, context: CallbackContext):
    # Storing Replyed Text From The User
    context.user_data["message_text"] = update.message.text
    update.message.reply_text("Please enter a time when bot should reminde")
    # What is Next Step
    return ENTER_TIME


def enter_time_handler(update: Update, context: CallbackContext):
    message_text = context.user_data["message_text"]
    # After Storing message_text in previous Step, We Send another message to the bot again (which is Time),
    # so the value in update.message.text now is Time
    time = datetime.datetime.strptime(update.message.text, '%d/%m/%Y %H:%M')
    # Storing Whole Data
    message_data = data_source.create_reminder(update.message.chat_id, message_text, time)
    update.message.reply_text("Your Reminder: " + message_data.__repr__())
    return ConversationHandler.END


def start_check_reminders_thread():
    thread = threading.Thread(target=check_reminders, args=())
    thread.daemon = True
    thread.start()


def check_reminders():
    while True:
        for reminder_data in data_source.get_all_reminders():
            if reminder_data.should_be_fired():
                data_source.fire_reminder(reminder_data.reminder_id)
                updater.bot.send_message(reminder_data.chat_id, reminder_data.message)
        time.sleep(TIME_SLEEP)


if __name__ == "__main__":
    # Activate Bot
    updater = Updater(TOKEN, use_context=True)
    # Add Command Handler (Which Function Will Be Called When Using Exact Command)
    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    
    # To Handle The Next Step After Start Command
    conv_handler = ConversationHandler(
        # entry_points: Which Function Will be Called when pressing an Exact Button According to Text
        # MessageHandler Read Received Text and Call Needed Function
        entry_points=[MessageHandler(Filters.regex(ADD_REMINDER_TEXT), add_reminder_handler)],
        # Which Function Will be Called when Sending Messages Between User and Bot
        states={
            ENTER_MESSAGE: [MessageHandler(Filters.all, enter_message_handler)],
            ENTER_TIME: [MessageHandler(Filters.all, enter_time_handler)]
            }, 
        fallbacks=[]
        )
    updater.dispatcher.add_handler(conv_handler)

    data_source.create_tables()   # Create Table for User After He Starts The Bot
    # updater.start_polling()   # Apply Updates
    run()
    start_check_reminders_thread()   # Work on Checking Reminders Behind The Scenes
