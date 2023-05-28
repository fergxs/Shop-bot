# Importing necessary modules and objects
import os
import handlers
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import config
from loader import dp, db, bot
import filters
import logging

# Setting up custom filters
filters.setup(dp)

# Defining host and port for the webhook in case the bot is hosted on Heroku
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 5000))

# Defining strings for user messages
user_message = 'User'
admin_message = 'Admin'

# A command handler for /start command
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    # Create a reply keyboard markup
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(user_message, admin_message)

    # Send a welcome message to the user
    await message.answer('''Hello! 👋

🤖 I am a bot-shop for selling goods of any category.

🛍️ To go to the catalog and choose the goods you like, use the command /menu.

💰 You can top up your account via Yandex.Checkout, Sberbank or Qiwi.

❓ Have questions? Not a problem! The /sos command will help you contact the admins, who will try to respond as quickly as possible.

🤝 Order a similar bot? Contact the developer <a href="https://t.me/NikolaySimakov">Nikolay Simakov</a>, he doesn't bite)))
    ''', reply_markup=markup)

# A message handler for 'user_message'
@dp.message_handler(text=user_message)
async def user_mode(message: types.Message):
    # Remove chat id from the list of admins if it's there
    cid = message.chat.id
    if cid in config.ADMINS:
        config.ADMINS.remove(cid)

    # Send a message about enabling user mode and remove the keyboard
    await message.answer('User mode enabled.', reply_markup=ReplyKeyboardRemove())

# A message handler for 'admin_message'
@dp.message_handler(text=admin_message)
async def admin_mode(message: types.Message):
    # Add chat id to the list of admins if it's not there yet
    cid = message.chat.id
    if cid not in config.ADMINS:
        config.ADMINS.append(cid)

    # Send a message about enabling admin mode and remove the keyboard
    await message.answer('Admin mode enabled.', reply_markup=ReplyKeyboardRemove())

# An on-startup function
async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    # Create tables in the database if they don't exist
    db.create_tables()

    # Remove and set a new webhook
    await bot.delete_webhook()
    await bot.set_webhook(config.WEBHOOK_URL)

# An on-shutdown function
async def on_shutdown():
    logging.warning("Shutting down..")
    # Delete the webhook and close the storage
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")

# The entry point of the script
if __name__ == '__main__':
    # If the bot is hosted on Heroku
    if "HEROKU" in list(os.environ.keys()):
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
    # If the bot is not hosted on Heroku, start polling
    else:
        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
