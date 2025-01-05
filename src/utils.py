import json
import logging
import re
from datetime import datetime
from fileinput import filename
from re import search
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def transactions_xlsx(filename: str) -> list:
    """
    Считывает Excel файл с транзакциями и возвращает список словарей этих транзакций
    :param filename:
    :return:
    """

    if len(filename) == 0 or not isinstance(filename, str):
        logging.warning("Пустое имя файла или неверный тип данных.")
        return []

    try:
        logging.info(f"Открытие файла {filename}")
        excel_data = pd.read_excel(filename)
        excel_data = excel_data.to_dict("records")
        logging.info(f"Файл {filename} успешно прочитан. Количество транзакций: {len(excel_data)}")
        return excel_data
    except FileNotFoundError:
        logging.error(f"Файл {filename} не найден.")
        return []


def web_search_xcl(transactions, input_search):
    """
    Проводит поиск по категориям, по всему Excel-файлу.
    :param transactions:
    :param input_search:
    :return: JSON строка
    """
    logging.info("Начало поиска по категориям.")
    list_result = []
    pattern = re.compile(re.escape(input_search), re.I)

    for transaction in transactions:
        description = transaction.get("Категория")
        if isinstance(description, str) and re.search(pattern, description):
            logging.debug(f"Транзакция добавлена в список результатов: {transaction}")
            list_result.append(transaction)

    logging.info(f"Поиск завершен. Найдено {len(list_result)} транзакций.")
    return json.dumps(list_result, ensure_ascii=False)


def num_card_account(transactions, user_input):
    """
    Вычисляет сумму всех операций по определенной банковской карте и
    возвращает значение в формате JSON.

    Функция принимает список транзакций, где каждая транзакция
    представлена в виде словаря. Пользователь вводит номер карты,
    после чего функция фильтрует все транзакции по этому номеру
    карты и суммирует округленные значения операций.

    Аргументы:
    transactions (list): Список транзакций, где каждая транзакция
                         представлена в виде словаря с ключами
                         'Номер карты' и 'Сумма операции с округлением'.
    user_input (str): Номер карты, для которой необходимо вычислить сумму транзакций.

    Возвращает:
    str: JSON-строка с суммой всех операций по введенному номеру карты, округленная до ближайшего целого.
    """
    logging.info(f"Начало подсчета суммы операций для карты {user_input}.")
    list_sum = []
    for transaction in transactions:
        if transaction["Номер карты"] == user_input:
            logging.debug(f"Добавление суммы операции: {transaction.get('Сумма операции с округлением')}")
            list_sum.append(transaction.get("Сумма операции с округлением"))

    res_sum = sum(list_sum)
    rounded_sum = round(res_sum)

    # Подготовка данных для возврата в формате JSON
    result = {"Номер карты": user_input, "Сумма операций": rounded_sum}

    logging.info(f"Подсчет завершен. Общая сумма: {rounded_sum}")
    return json.dumps(result, ensure_ascii=False)
