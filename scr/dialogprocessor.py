from telegram import Update, ParseMode, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from scr.ClosureProcessor import ClosureProcessor


class DialogProcessor:
    INIT, FORWARD, CLOSURE = map(chr, range(3))

    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.costs_names = ["Расход р/c", "Расход с корп. карты", "Расход налички"]
        self.cash_income = ["Поступление налички"]
        self.closure = ["Закрыть объект"]
        self.funny_story = ["Анекдот дня"]
        self.current_task = ''
        self.current_state = self.INIT
        self.closure_processor = ClosureProcessor()

    def __forward(self, update: Update, context: CallbackContext):
        update.message.reply_text("Принято, спасибо!")
        message = f'<b>{self.current_task}</b>\n' \
                  f'Автор: {update.message.from_user.first_name}(@{update.message.from_user.username})\n' \
                  f'Сообщение:\n{update.message.text}'
        context.bot.send_message(chat_id=self.chat_id, text=message, parse_mode=ParseMode.HTML)
        self.current_state = self.INIT

    def __process_costs(self, update: Update):
        update.message.reply_text("Укажите сумму, на что потрачено и адрес объекта, к которому относится расход")
        self.current_state = self.FORWARD

    def __process_cash_income(self, update: Update):
        update.message.reply_text("Укажите сумму и адрес объекта, к которому относится поступление")
        self.current_state = self.FORWARD

    def process_message(self, update: Update, context: CallbackContext):
        if self.process_buttons(update) or self.current_state == self.INIT:
            return
        if self.current_state == self.FORWARD:
            self.__forward(update, context)
        elif self.current_state == self.CLOSURE:
            inner_state = self.closure_processor.process_message(update, context)
            self.current_state = self.INIT if inner_state == ClosureProcessor.END else self.CLOSURE;

    def process_buttons(self, update: Update):
        if update.message.text in self.costs_names:
            self.__process_costs(update)
        elif update.message.text in self.cash_income:
            self.__process_cash_income(update)
        elif update.message.text in self.closure:
            self.current_state = 'closure'
        elif update.message.text in self.funny_story:
            pass
        else:
            return False
        self.current_task = update.message.text
        return True

    def start(self, update: Update, context: CallbackContext):
        reply_markup = ReplyKeyboardMarkup(self.get_keyboard())
        update.message.reply_text("Start handler, Choose a route", reply_markup=reply_markup)
        self.current_state = self.INIT

    def get_keyboard(self):
        return [self.costs_names, self.cash_income, self.closure, self.funny_story]




