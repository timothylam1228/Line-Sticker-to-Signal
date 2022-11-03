import os

from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
from telegram.bot import Bot, BotCommand

from commands.cmd import *

load_dotenv()

APP_ENV_IS_TEST = os.environ.get('APP_ENV') == 'test'
TOKEN = os.environ.get('TOKEN')
PORT = int(os.environ.get('PORT', '8443'))
# print()
commands = [
('start','show start message'),('help', 'show all command'),('convert','convert Line sticker to Telegram'), ('signal','convert Line sticker to Signal')
]
def main():
    if APP_ENV_IS_TEST:
        print(TOKEN)
        print(PORT)
        print('Running in test environment')
    else:
        print('Running in production environment')

    try:
        updater = Updater(TOKEN, use_context=True)
        bot = Bot(TOKEN)
        bot.set_my_commands(commands)

        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help))
        dp.add_handler(CommandHandler("updatelog", updatelog))
        dp.add_handler(CommandHandler("convert", convert, run_async=True))
        dp.add_handler(CommandHandler("signal", convert_signal, run_async=True, pass_args=True))
        updater.start_polling()
        updater.idle()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()

'''
help - show all command
start - show start message
convert - convert Line sticker to Telegram
signal - convert Line sticker to Signal
'''