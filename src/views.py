import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from alpha_vantage.timeseries import TimeSeries
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

from src.utils import transactions_xlsx

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv("E:/pycharm_project/transaction_analysis_web/.env")

# Получите API ключи из .env
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


def load_user_settings():
    """Загружает настройки пользователя из файла user_settings.json"""
    try:
        with open("E:/pycharm_project/transaction_analysis_web/src/user_settings.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Файл user_settings.json не найден")
        return None
    except json.JSONDecodeError:
        logging.error("Ошибка декодирования JSON")
        return None


def get_exchange_rate():
    """
    Запрашивает текущий курс валют с использованием API
    :return: Словарь с курсами валют для пользовательских валют или None в случае ошибки
    """
    logging.debug("Запрос курса валют")

    # Загрузить настройки пользователя
    user_settings = load_user_settings()
    if not user_settings:
        logging.error("Не удалось загрузить настройки пользователя")
        return None

    # Получить список валют пользователя
    user_currencies = user_settings.get("user_currencies", ["USD"])

    # Формировать базовый URL
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/USD"
    response = requests.get(url)

    if response.status_code == 200:
        logging.info("Курс валют успешно получен")
        data = response.json()

        # Выборка только нужных валют
        filtered_rates = {
            currency: data["conversion_rates"].get(currency)
            for currency in user_currencies
            if currency in data["conversion_rates"]
        }

        if len(filtered_rates) != len(user_currencies):
            missing_currencies = set(user_currencies) - filtered_rates.keys()
            logging.warning(f"Некоторые валюты не были найдены: {', '.join(missing_currencies)}")

        return filtered_rates
    else:
        logging.error(f"Не удалось получить курс валют, статус: {response.status_code}")
        return None


def get_stock_price(symbol):
    """
    Возвращает текущую цену акции для указанного символа.

    Параметры:
    symbol (str): символьное обозначение акции, для которой нужно получить цену.

    Возвращает:
    float: текущая цена акции.

    Исключения:
    ValueError: если не указан API ключ.
    RuntimeError: если произошла ошибка при получении данных для символа.
    """

    if not ALPHA_VANTAGE_API_KEY:
        logging.error("Необходимо указать API ключ в .env файле.")
        raise ValueError("Необходимо указать API ключ в .env файле.")

    ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format="json")
    logging.info(f"Запрос цены акции для символа: {symbol}")

    try:
        # Получение текущей цены акции
        data, _ = ts.get_quote_endpoint(symbol=symbol)
        price = data["05. price"]
        logging.info(f"Успешно получена цена акции для {symbol}: {price}")
    except Exception as e:
        logging.error(f"Ошибка при получении данных для {symbol}: {e}")
        raise RuntimeError(f"Ошибка при получении данных для {symbol}: {e}")

    return float(price)


def fetch_currency_rates():
    """
    Функция-оболочка для получения курса валют.
    :return:
    """
    return get_exchange_rate()


def fetch_stock_prices():
    '''
    Функция-оболочка для получения цен на акции.
    :return:
    '''
    return get_stock_prices()


def get_greeting(hour):
    """
    Возвращает приветствие на основе переданного времени суток.
    :param hour:
    :return:
    """
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def parse_datetime(date_str):
    """
    Парсит строку с датой в объект datetime.
    :param date_str:
    :return:
    """
    logging.debug(f"Парсинг даты: {date_str}")
    datetime_obj = datetime.strptime(date_str.strip(), "%d-%m-%Y %H:%M:%S")
    return datetime_obj


def process_excel_data(excel_file_path, specific_date):
    """
    Обрабатывает данные транзакций и возвращает отчет за период от введенной даты до конца месяца в формате JSON.
    :param excel_file_path: путь к Excel файлу с данными транзакций
    :param specific_date: дата, с которой начинается отчет
    :return: JSON строка с отфильтрованными данными
    """
    logging.info(f"Начало обработки файла: {excel_file_path}")

    try:
        df = pd.read_excel(excel_file_path)
        logging.info("Excel файл успешно загружен.")

        # Преобразование строковой даты в формат datetime
        start_date = datetime.strptime(specific_date, "%d.%m.%Y")
        logging.info(f"Дата начала отчетного периода: {start_date}")

        # Вычисление последнего дня месяца
        end_date = (start_date + relativedelta(months=1)) - pd.Timedelta(days=1)
        logging.info(f"Дата окончания отчетного периода: {end_date}")

        # Фильтрация данных по дате операции от заданной до конца месяца
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
        logging.info(f"Данные отфильтрованы. Количество записей: {len(filtered_df)}")

        # Преобразование отфильтрованных данных в JSON формат
        result_json = filtered_df.to_json(orient="records", date_format="iso", force_ascii=False)
        logging.info("Данные конвертированы в JSON формат.")

        return result_json

    except Exception as e:
        logging.error(f"Произошла ошибка при обработке файла: {e}")
        raise
