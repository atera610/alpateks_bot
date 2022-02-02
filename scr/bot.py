from dotenv import dotenv_values
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler, \
    CallbackContext
import logging
import urllib3
import json

config = dotenv_values('../.env')
tg_token = config['TELEGRAM_BOT_TOKEN']
tg_chat_id = config['TELEGRAM_CHAT_ID']

funny_story_url = "http://rzhunemogu.ru/RandJSON.aspx?CType=1"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

main_menu_text = "Вернуться в основное меню"
expenses_one_text = "Расход р/c"
expenses_two_text = "Расход с корп. карты"
expenses_three_text = "Расход налички"
income_text = "Поступление налички"
closure_text = "Закрыть объект"
funny_story_text = "Внимание, анекдот!"

cost_one_button = KeyboardButton(expenses_one_text)
cost_two_button = KeyboardButton(expenses_two_text)
cost_three_button = KeyboardButton(expenses_three_text)
cash_button = KeyboardButton(income_text)
closure_button = KeyboardButton(closure_text)
story_button = KeyboardButton(funny_story_text)

button_names = [expenses_one_text, expenses_two_text, expenses_three_text, income_text, closure_text, funny_story_text]
keyboard = [[cost_one_button, cost_two_button, cost_three_button], [cash_button], [closure_button], [story_button]]

INIT, FORWARD, CLOSURE_DIALOG = map(chr, range(3))
ADDRESS, PARTNER_NAME, MONEY, DATE, COMPANY_NAME, DEBT, COLLECT_FORWARD, END = map(chr, range(3, 11))

CURRENT_TASK, CURRENT_FEATURE = map(chr, range(11, 13))


def start(update: Update, context: CallbackContext) -> str:
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text("Привет! Со мной можно общаться через кнопки в меню. ", reply_markup=reply_markup)
    return INIT


def stop(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Спасибо за работу, пока!')
    return ConversationHandler.END


def process_expenses(update: Update, context: CallbackContext) -> str:
    context.user_data[CURRENT_TASK] = update.message.text
    update.message.reply_text("Укажите сумму, на что потрачено и адрес объекта, к которому относится расход")
    return FORWARD


def process_cash_income(update: Update, context: CallbackContext) -> str:
    context.user_data[CURRENT_TASK] = update.message.text
    update.message.reply_text("Укажите сумму и адрес объекта, к которому относится поступление")
    return FORWARD


def process_story(update: Update, context: CallbackContext) -> str:
    try:
        response = urllib3.PoolManager().request('GET', funny_story_url)
        decoded_json = response.data.decode('windows-1251')
        message = json.loads(decoded_json.replace('\r\n', '\\r\\n'))['content']
    except Exception as e:
        logging.error("Could not get funny story", e)
        message = "Что-то пошло не так, попробуйте позже"
    update.message.reply_text(message)

    return INIT


def process_buttons(update: Update, context: CallbackContext):
    if update.message.text in [expenses_one_text, expenses_two_text, expenses_three_text]:
        return process_expenses(update, context)
    if update.message.text == income_text:
        return process_cash_income(update, context)
    if update.message.text == closure_text:
        return closure_selected(update, context)
    if update.message.text == funny_story_text:
        return process_story(update, context)


def forward(update: Update, context: CallbackContext) -> str:
    if update.message.text in button_names:
        return process_buttons(update, context)

    update.message.reply_text("Принято, спасибо!")
    if CURRENT_TASK in context.user_data:
        message = f'<b>{context.user_data[CURRENT_TASK]}</b>\n' \
                  f'{update.message.text}\n' \
                  f'{update.message.from_user.first_name}(@{update.message.from_user.username})\n'
        context.bot.send_message(chat_id=tg_chat_id, text=message, parse_mode=ParseMode.HTML)
    return INIT


def closure_handler(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("На каком адресе закончена работа?", reply_markup=ReplyKeyboardMarkup([[main_menu_text]]))
    return ADDRESS


def closure_selected(update: Update, context: CallbackContext) -> str:
    closure_handler(update, context)
    return CLOSURE_DIALOG


def process_address(update: Update, context: CallbackContext) -> str:
    context.user_data[ADDRESS] = update.message.text
    update.message.reply_text("Название юрлица заказчика")
    return PARTNER_NAME


def process_partner_name(update: Update, context: CallbackContext) -> str:
    context.user_data[PARTNER_NAME] = update.message.text
    update.message.reply_text("Сколько нам должен?")
    return MONEY


def process_money(update: Update, context: CallbackContext) -> str:
    context.user_data[MONEY] = update.message.text
    update.message.reply_text("Когда примерно должно прийти?")
    return DATE


def process_date(update: Update, context: CallbackContext) -> str:
    context.user_data[DATE] = update.message.text
    update.message.reply_text("Наше юрлицо", reply_markup=ReplyKeyboardMarkup([["ИП", "ООО"]], one_time_keyboard=True))
    return COMPANY_NAME


def process_company_name(update: Update, context: CallbackContext) -> str:
    context.user_data[COMPANY_NAME] = update.message.text
    update.message.reply_text("Кому и сколько должны за работу?"
                              " (Фамилия, Имя работника, сумма. Если платить с налогами, укажите на сколько делить)")
    return DEBT


def process_debt(update: Update, context: CallbackContext) -> str:
    if update.message.text == "Запланировать расход":
        update.message.reply_text("Кому и сколько должны за работу? "
                                  "(Фамилия, Имя работника, сумма. Если платить с налогами, укажите на сколько делить)")
        return DEBT
    elif update.message.text == closure_text:
        return collect_forward_data(update, context)
    if DEBT in context.user_data:
        context.user_data[DEBT] = f'{context.user_data[DEBT]},\n {update.message.text}'
    else:
        context.user_data[DEBT] = update.message.text
    update.message.reply_text("Принято, спасибо. Запланировать ещё расходы по этому объекту?",
                              reply_markup=ReplyKeyboardMarkup([["Запланировать расход", "Закрыть объект "]],
                                                               one_time_keyboard=True))


def collect_forward_data(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    if ADDRESS not in user_data or COMPANY_NAME not in user_data or PARTNER_NAME not in user_data or DATE not in user_data:
        message = f'Вы заполнили не вю информацию, попробуйте ещё раз'
        update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(keyboard))
    else:
        closure_info = f'<b>Завершили работы</b> по адресу: {user_data[ADDRESS]}\n' \
                       f'Ожидаем поступления на счёт {user_data[COMPANY_NAME]} от {user_data[PARTNER_NAME]} ' \
                       f'в размере {user_data[MONEY]} примерно {user_data[DATE]}.\n' \
                       f'Мы должны:\n{user_data[DEBT] if DEBT in user_data else ""} '
        message = f'{closure_info}\n<i>{update.message.from_user.first_name}(@{update.message.from_user.username})</i>'
        update.message.reply_text(message, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(keyboard))
        context.bot.send_message(chat_id=tg_chat_id, text=message, parse_mode=ParseMode.HTML)
    user_data.clear()
    return END


def stop_inner(update: Update, context: CallbackContext) -> str:
    update.message.reply_text("Хорошо!", reply_markup=ReplyKeyboardMarkup(keyboard))
    return END


if __name__ == '__main__':
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    closure_conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(main_menu_text), stop_inner), MessageHandler(Filters.text, process_address)],
        states={
            PARTNER_NAME: [MessageHandler(Filters.regex(main_menu_text), stop_inner), MessageHandler(Filters.text, process_partner_name)],
            MONEY: [MessageHandler(Filters.regex(main_menu_text), stop_inner), MessageHandler(Filters.text, process_money)],
            DATE: [MessageHandler(Filters.regex(main_menu_text), stop_inner), MessageHandler(Filters.text, process_date)],
            COMPANY_NAME: [MessageHandler(Filters.text, process_company_name)],
            DEBT: [MessageHandler(Filters.text, process_debt)],
            COLLECT_FORWARD: [MessageHandler(Filters.text, collect_forward_data)]
        },
        fallbacks=[MessageHandler(Filters.text, collect_forward_data),
                   MessageHandler(Filters.regex(main_menu_text), stop_inner)],
        map_to_parent={
            END: INIT
        }
    )
    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            INIT: [MessageHandler(Filters.regex(expenses_one_text)
                                  | Filters.regex(expenses_two_text)
                                  | Filters.regex(expenses_three_text),
                                  process_expenses),
                   MessageHandler(Filters.regex(income_text), process_cash_income),
                   MessageHandler(Filters.regex(closure_text), closure_selected),
                   MessageHandler(Filters.regex(funny_story_text), process_story)],
            FORWARD: [MessageHandler(Filters.text, forward)],
            CLOSURE_DIALOG: [closure_conv]
        },
        fallbacks=[CommandHandler('stop', stop)],
    )
    dispatcher.add_handler(main_conv)
    updater.start_polling()
    updater.idle()
