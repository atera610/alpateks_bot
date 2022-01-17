from telegram import Update
from telegram.ext import CallbackQueryHandler, CallbackContext


class ClosureProcessor:
    ADDRESS, PARTNER_NAME, MONEY, DATE, COMPANY_NAME, DEBT, COLLECT_FORWARD, END = map(chr, range(8))

    def __init__(self):
        self.current_state = self.ADDRESS

    def process_message(self, update: Update, context: CallbackContext):
        return self.current_state

    def __ask_address(self):
        pass

    def __ask_partner_name(self):
        pass

    def __ask_money(self):
        pass

    def __ask_date(self):
        pass

    def __ask_company_name(self):
        pass

    def __ask_debt(self):
        pass

    def __collect_forward_data(self):
        pass

    def end(self):
        pass

    def get_states(self):
        return {
                self.ADDRESS: [CallbackQueryHandler(self.__ask_address)],
                self.PARTNER_NAME: [CallbackQueryHandler(self.__ask_partner_name)],
                self.MONEY: [CallbackQueryHandler(self.__ask_money)],
                self.DATE: [CallbackQueryHandler(self.__ask_date)],
                self.COMPANY_NAME: [CallbackQueryHandler(self.__ask_company_name)],
                self.DEBT: [CallbackQueryHandler(self.__ask_debt)],
                self.COLLECT_FORWARD: [CallbackQueryHandler(self.__collect_forward_data)],
            }

