from dotenv import dotenv_values
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler
import logging
from dialogprocessor import DialogProcessor


config = dotenv_values('../.env')
tg_token = config['TELEGRAM_BOT_TOKEN']
tg_chat_id = config['TELEGRAM_CHAT_ID']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


if __name__ == '__main__':
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    dialog_processor = DialogProcessor(chat_id=tg_chat_id)
    dispatcher.add_handler(CommandHandler("start", dialog_processor.start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, dialog_processor.process_message))
    updater.dispatcher.add_handler(CallbackQueryHandler(dialog_processor.process_inline_buttons))

    updater.start_polling()
    updater.idle()
