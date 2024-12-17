import logging
from collections import defaultdict
from datetime import datetime

import pandas as pd

# Настройка логгирования
logging.basicConfig(
    filename="app.log", filemode="a", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


def result_report_to_file(file="res_report.txt"):
    """
    Декоратор, сохраняющий результат функции в файл.

    :param file: имя файла, в который записывается результат
    :return: обёрнутая функция
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logging.info(f"Вызов функции {func.__name__} с аргументами {args} и {kwargs}")
            result = func(*args, **kwargs)
            logging.info(f"Функция {func.__name__} вернула {result}")
            with open(file, "w") as f:
                f.write(str(result))
            return result

        return wrapper

    return decorator


def load_transactions(filepath):
    """
    Загрузка транзакций из Excel файла.

    :param filepath: путь к файлу Excel
    :return: DataFrame с загруженными транзакциями
    :raises: Исключение в случае ошибки загрузки
    """
    try:
        logging.info(f"Загрузка транзакций из {filepath}")
        transactions = pd.read_excel(filepath, parse_dates=["Дата операции"], date_format="%d.%m.%Y %H:%M:%S")
        logging.info("Транзакции успешно загружены")
        return transactions
    except Exception as e:
        logging.error(f"Ошибка при загрузке транзакций: {e}")
        raise


@result_report_to_file("category_spending_report.txt")
def rep_category_spending(transactions, name_category, date):
    """
    Расчёт расходов по указанной категории до заданной даты.

    :param transactions: DataFrame с транзакциями
    :param name_category: название категории
    :param date: конечная дата расчёта
    :return: строка с общими расходами по категории
    :raises: Исключение в случае ошибки
    """
    try:
        logging.info(f"Расчёт расходов по категории {name_category} до {date}")
        category_spending = transactions[
            (transactions["Категория"] == name_category) & (transactions["Дата операции"] <= date)
        ]["Сумма операции"].sum()
        return f"Общие расходы на категорию '{name_category}': {category_spending}"
    except Exception as e:
        logging.error(f"Ошибка в rep_category_spending: {e}")
        raise


@result_report_to_file("weekday_spending_report.txt")
def rep_spending_on_weekdays(transactions, date):
    """
    Расчёт расходов по дням недели до заданной даты.

    :param transactions: DataFrame с транзакциями
    :param date: конечная дата расчёта
    :return: строка с расходами по дням недели
    :raises: Исключение в случае ошибки
    """
    try:
        logging.info(f"Расчёт расходов по дням недели до {date}")
        transactions["День недели"] = transactions["Дата операции"].apply(lambda x: x.weekday())
        weekday_spending = (
            transactions[transactions["Дата операции"] <= date].groupby("День недели")["Сумма операции"].sum()
        )
        return weekday_spending.to_string()
    except Exception as e:
        logging.error(f"Ошибка в rep_spending_on_weekdays: {e}")
        raise


@result_report_to_file("workweek_or_weekend_spending_report.txt")
def rep_spend_on_working_or_weekends(transactions, date):
    """
    Расчёт расходов на рабочие и выходные дни до заданной даты.

    :param transactions: DataFrame с транзакциями
    :param date: конечная дата расчёта
    :return: строка с расходами по типу дня (рабочий/выходной)
    :raises: Исключение в случае ошибки
    """
    try:
        logging.info(f"Расчёт расходов на рабочие и выходные до {date}")
        transactions["День недели"] = transactions["Дата операции"].apply(lambda x: x.weekday())
        transactions["Тип дня"] = transactions["День недели"].apply(lambda x: "Рабочий" if x < 5 else "Выходной")
        spending_by_day_type = (
            transactions[transactions["Дата операции"] <= date].groupby("Тип дня")["Сумма операции"].sum()
        )
        return spending_by_day_type.to_string()
    except Exception as e:
        logging.error(f"Ошибка в rep_spend_on_working_or_weekends: {e}")
        raise
