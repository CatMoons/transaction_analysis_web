import json
import logging
import re

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def analyze_cashback(data, year, month):
    """
    Анализирует данные по операциям и рассчитывает суммы кэшбэка для каждой категории за указанный месяц.
    :param data:
    :param year:
    :param month:
    :return:
    """
    logging.info("Начало анализа кэшбэка за %d-%02d", year, month)

    try:
        df = pd.read_excel(data)
        logging.info("Данные успешно загружены из '%s'", data)
    except Exception as e:
        logging.error("Ошибка загрузки данных: %s", e)
        return None

    try:
        # Преобразуем столбец с датами в формат datetime
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        logging.info("Столбец 'Дата операции' успешно преобразован в datetime")
    except Exception as e:
        logging.error("Ошибка преобразования даты: %s", e)
        return None

    # Фильтрация данных по заданному году и месяцу
    filtered_df = df[(df["Дата операции"].dt.year == year) & (df["Дата операции"].dt.month == month)]
    logging.info("Данные отфильтрованы: %d записей в %d-%02d", len(filtered_df), year, month)

    # Группировка данных по категории и суммирование кэшбэка
    try:
        cashback_summary = filtered_df.groupby("Категория")["Кэшбэк"].sum()
        logging.info("Кэшбэк успешно рассчитан")
    except Exception as e:
        logging.error("Ошибка расчета кэшбэка: %s", e)
        return None

    cashback_dict = cashback_summary.to_dict()
    cashback_json = json.dumps(cashback_dict, ensure_ascii=False)

    logging.info("Анализ завершён успешно")
    return cashback_json


def extract_phone_numbers(description):
    """
    Извлекает телефонные номера из строки описания.
    :param description:
    :return:
    """
    phone_pattern = r"(?:(?:8|\+7)[\- ])?(?:\(?\d{3}\)?[\- ])[\d\- ]{7,10}"
    phone_numbers = re.findall(phone_pattern, description)
    logging.debug(f"Extracted phone numbers: {phone_numbers} from description: {description}")
    return phone_numbers


def get_transactions_with_phones(file_path):
    """
    Извлекает транзакции с телефонными номерами из файла Excel.
    :param file_path:
    :return:
    """
    # Чтение Excel файла
    df = pd.read_excel(file_path)

    # Проверка, что файл содержит нужный столбец
    if "Описание" not in df.columns:
        raise ValueError("Нет столбца 'Описание' в файле.")

    transactions_with_phones = []

    # Обработка каждой строки
    for index, row in df.iterrows():
        description = row["Описание"].strip()
        logging.debug(f"Обработка строки {index}: {description}")
        phone_numbers = extract_phone_numbers(description)

        if phone_numbers:
            transaction_info = {"index": index, "description": description, "phone_numbers": phone_numbers}
            transactions_with_phones.append(transaction_info)
            logging.debug(f"Добавлена транзакция с телефонами: {transaction_info}")

    # Возвращаем JSON
    return json.dumps(transactions_with_phones, ensure_ascii=False, indent=4)
