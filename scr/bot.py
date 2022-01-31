import urllib

from dotenv import dotenv_values
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler, \
    CallbackContext
import logging

config = dotenv_values('../.env')
tg_token = config['TELEGRAM_BOT_TOKEN']
tg_chat_id = config['TELEGRAM_CHAT_ID']

funny_story_chat_id = -1001060960001

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

cost_one_button = KeyboardButton("Расход р/c")
cost_two_button = KeyboardButton("Расход с корп. карты")
cost_three_button = KeyboardButton("Расход налички")
cash_button = KeyboardButton("Поступление налички")
closure_button = KeyboardButton("Закрыть объект")
story_button = KeyboardButton("Анекдот дня")
keyboard = [[cost_one_button, cost_two_button, cost_three_button], [cash_button], [closure_button], [story_button]]

INIT, FORWARD, CLOSURE_DIALOG = map(chr, range(3))
ADDRESS, PARTNER_NAME, MONEY, DATE, COMPANY_NAME, DEBT, COLLECT_FORWARD, END = map(chr, range(3, 11))

CURRENT_TASK, CURRENT_FEATURE = map(chr, range(11, 13))


def start(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text("Start handler, Choose a route", reply_markup=reply_markup)
    return INIT


def closure_handler(update: Update, context: CallbackContext):
    update.message.reply_text("На каком адресе закончена работа?")
    return ADDRESS


def closure_selected(update: Update, context: CallbackContext):
    closure_handler(update, context)
    return CLOSURE_DIALOG

def process_story(update: Update, context: CallbackContext):
    # context.bot.forward_message(chat_id=tg_chat_id, from_chat_id=funny_story_chat_id)

    return INIT

def forward(update: Update, context: CallbackContext):
    update.message.reply_text("Принято, спасибо!")
    if CURRENT_TASK in context.user_data:
        message = f'<b>{context.user_data[CURRENT_TASK]}</b>\n' \
                  f'{update.message.text}\n' \
                  f'{update.message.from_user.first_name}(@{update.message.from_user.username})\n'
        context.bot.send_message(chat_id=tg_chat_id, text=message, parse_mode=ParseMode.HTML)
    return INIT


def process_costs(update: Update, context: CallbackContext):
    context.user_data[CURRENT_TASK] = update.message.text
    update.message.reply_text("Укажите сумму, на что потрачено и адрес объекта, к которому относится расход")
    return FORWARD


def process_cash_income(update: Update, context: CallbackContext):
    context.user_data[CURRENT_TASK] = update.message.text
    update.message.reply_text("Укажите сумму и адрес объекта, к которому относится поступление")
    return FORWARD


def process_address(update: Update, context: CallbackContext):
    context.user_data[ADDRESS] = update.message.text
    update.message.reply_text("Название юрлица заказчика")
    return PARTNER_NAME


def process_partner_name(update: Update, context: CallbackContext):
    context.user_data[PARTNER_NAME] = update.message.text
    update.message.reply_text("Сколько нам должен?")
    return MONEY


def process_money(update: Update, context: CallbackContext):
    context.user_data[MONEY] = update.message.text
    update.message.reply_text("Когда примерно должно прийти?")
    return DATE


def process_date(update: Update, context: CallbackContext):
    context.user_data[DATE] = update.message.text
    update.message.reply_text("Наше юрлицо", reply_markup=ReplyKeyboardMarkup([["ИП", "ООО"]]))
    return COMPANY_NAME


def process_company_name(update: Update, context: CallbackContext):
    context.user_data[COMPANY_NAME] = update.message.text
    update.message.reply_text("Кому и сколько должны за работу?"
                              " (Фамилия, Имя работника, сумма. Если платить с налогами, укажите на сколько делить)",
                              reply_markup=ReplyKeyboardMarkup([["Должны ещё кому-то", "Закрыть объект "]]))
    return DEBT


def process_debt(update: Update, context: CallbackContext):
    if update.message.text == "Должны ещё кому-то":
        update.message.reply_text("Кому и сколько должны за работу?"
                                  " (Фамилия, Имя работника, сумма. Если платить с налогами, укажите на сколько делить)",
                                  reply_markup=ReplyKeyboardMarkup([["Должны ещё кому-то", "Закрыть объект "]]))
        return DEBT
    elif update.message.text == "Закрыть объект":
        return collect_forward_data(update, context)
    if DEBT in context.user_data:
        context.user_data[DEBT] = f'{context.user_data[DEBT]}, {update.message.text}'
    else:
        context.user_data[DEBT] = update.message.text


def collect_forward_data(update: Update, context: CallbackContext):
    user_data = context.user_data
    closure_info = f'<b>Завершили работы</b> по адресу: {user_data[ADDRESS]}\n' \
                   f'Ожидаем поступления на счёт {user_data[COMPANY_NAME]} от {user_data[PARTNER_NAME]} ' \
                   f'в размере {user_data[MONEY]} примерно {user_data[DATE]}.\n' \
                   f'Мы должны:{user_data[DEBT]} '
    message = f'{closure_info}\n{update.message.from_user.first_name}(@{update.message.from_user.username})'
    update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(keyboard))
    context.bot.send_message(chat_id=tg_chat_id, text=message, parse_mode=ParseMode.HTML)
    return END


def stop(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Okay, bye.')
    return ConversationHandler.END


if __name__ == '__main__':
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    closure_conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.text, process_address)],
        states={
            PARTNER_NAME: [MessageHandler(Filters.text, process_partner_name)],
            MONEY: [MessageHandler(Filters.text, process_money)],
            DATE: [MessageHandler(Filters.text, process_date)],
            COMPANY_NAME: [MessageHandler(Filters.text, process_company_name)],
            DEBT: [MessageHandler(Filters.text, process_debt)],
            COLLECT_FORWARD: [MessageHandler(Filters.text, collect_forward_data)]
        },
        fallbacks=[MessageHandler(Filters.text, collect_forward_data)],
        map_to_parent={
            END: INIT
        }
    )
    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INIT: [MessageHandler(Filters.regex('Расход р/c')
                                  | Filters.regex('Расход с корп. карты')
                                  | Filters.regex('Расход налички'),
                                  process_costs),
                   MessageHandler(Filters.regex('Поступление налички'), process_cash_income),
                   MessageHandler(Filters.regex('Закрыть объект'), closure_selected),
                   MessageHandler(Filters.text, process_story)],
            FORWARD: [MessageHandler(Filters.text, forward)],
            CLOSURE_DIALOG: [closure_conv]
        },
        fallbacks=[CommandHandler('stop', stop)],
    )
    dispatcher.add_handler(main_conv)
    updater.start_polling()
    updater.idle()
