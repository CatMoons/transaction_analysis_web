from datetime import datetime

from reports import (load_transactions, rep_category_spending, rep_spend_on_working_or_weekends,
                     rep_spending_on_weekdays)
from services import analyze_cashback, extract_phone_numbers, get_transactions_with_phones
from utils import num_card_account, transactions_xlsx, web_search_xcl
from views import get_greeting, parse_datetime, process_excel_data

file_path = "E:/pycharm_project/transaction_analysis_web/data/operations.xlsx"
file_open_xlsx = transactions_xlsx(file_path)
load_transaction = load_transactions(file_path)

date_now = datetime.now().hour
date_input = "24.11.2021"

input_search = "Фастфуд"

input_card = "*4556"

year = 2021
month = 5


def main():
    print(get_greeting(date_now))
    print(process_excel_data(file_path, date_input))
    print(web_search_xcl(file_open_xlsx, input_search))
    print(num_card_account(file_open_xlsx, input_card))
    print(analyze_cashback(file_path, year, month))
    print(get_transactions_with_phones(file_path))
    print(rep_category_spending(load_transaction, input_search, date_input))
    print(rep_spending_on_weekdays(load_transaction, date_input))
    print(rep_spend_on_working_or_weekends(load_transaction, date_input))


if __name__ == "__main__":
    main()
