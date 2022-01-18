from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, ReplyKeyboardMarkup
from telegram.ext import CallbackContext


class Closure:
    def __init__(self):
        self.address = ""
        self.partner_name = ""
        self.money = ""
        self.date = ""
        self.company_name = ""
        self.people_to_pay = []

    def __str__(self):
        return f'<b>Завершили работы</b> по адресу: {self.address}\n' \
               f'Ожидаем поступления на счёт {self.company_name} от {self.partner_name} ' \
               f'в размере {self.money} примерно {self.date}.\n' \
               f'Мы должны: ' + ', '.join(self.people_to_pay)


class ClosureProcessor:

    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.states = ["INIT", "ADDRESS", "PARTNER_NAME", "MONEY", "DATE", "COMPANY_NAME",
                       "DEBT", "COLLECT_FORWARD", "END"]
        self.state_index = 0
        self.method_by_stage = {
            "INIT": self.init_dialog,
            "ADDRESS": self.process_address,
            "PARTNER_NAME": self.process_partner_name,
            "MONEY": self.process_money,
            "DATE": self.process_date,
            "COMPANY_NAME": self.process_company_name,
            "DEBT": self.process_debt,
            "COLLECT_FORWARD": self.collect_forward_data,
            "END": self.end
        }
        comp_choose_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ИП", callback_data='ИП'),
            InlineKeyboardButton("ООО", callback_data='ООО'),
        ]])
        debt_keyboard = ReplyKeyboardMarkup([["Должны ещё кому-то", "Закрыть объект"]])

        self.question_by_stage = {
            "ADDRESS":  "На каком адресе закончена работа?",
            "PARTNER_NAME": "Название юрлица заказчика",
            "MONEY":   "Сколько нам должен?",
            "DATE":   "Когда примерно должно прийти?",
            "COMPANY_NAME": "Наше юрлицо",
            "DEBT":  "Кому и сколько должны за работу? (Фамилия, Имя работника, сумма. Если платить с"
                    " налогами, укажите на сколько делить)"
        }
        self.keyboard_by_stage = {
            "COMPANY_NAME": comp_choose_keyboard,
            "DEBT":  debt_keyboard
        }
        self.closure = Closure()
        self.closure_finished = False

    def process_message(self, update: Update, context: CallbackContext):
        self.method_by_stage[self.states[self.state_index]](update, context)
        state = self.states[self.state_index]

        if state in self.keyboard_by_stage:
            context.bot.send_message(chat_id=update.effective_chat.id, text=self.question_by_stage[state], reply_markup=self.keyboard_by_stage[state])
        elif state in self.question_by_stage:
            context.bot.send_message(chat_id=update.effective_chat.id, text=self.question_by_stage[state])
        elif state == 'COLLECT_FORWARD':
            self.method_by_stage['COLLECT_FORWARD'](update, context)

    def init_dialog(self, update: Update, context: CallbackContext):
        self.state_index += 1

    def process_address(self, update: Update, context: CallbackContext):
        self.closure.address = update.message.text
        self.state_index += 1

    def process_partner_name(self, update: Update, context: CallbackContext):
        self.closure.partner_name = update.message.text
        self.state_index += 1

    def process_money(self, update: Update, context: CallbackContext):
        self.closure.money = update.message.text
        self.state_index += 1

    def process_date(self, update: Update, context: CallbackContext):
        self.closure.date = update.message.text
        self.state_index += 1

    def process_company_name(self, update: Update, context: CallbackContext):
        self.closure.company_name = update.callback_query.data
        self.state_index += 1

    def process_debt(self, update: Update, context: CallbackContext):
        if update.message.text == "Должны ещё кому-то":
            return
        elif update.message.text == "Закрыть объект":
            self.state_index += 1
            return
        self.closure.people_to_pay.append(update.message.text)

    def collect_forward_data(self, update: Update, context: CallbackContext):
        message = f'{self.closure}\n{update.message.from_user.first_name}(@{update.message.from_user.username})'
        context.bot.send_message(chat_id=self.chat_id, text=message, parse_mode=ParseMode.HTML)
        self.state_index += 1

    def end(self, update: Update, context: CallbackContext):
        self.state_index = 0

