import json
import os
from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest
import requests

from src.views import (get_exchange_rate, get_greeting, get_stock_price, load_user_settings, parse_datetime,
                       process_excel_data)


# Тестирование функции load_user_settings
def test_load_user_settings_success():
    """
    Тест для функции load_user_settings.
    Проверяет успешное считывание настроек пользователя из файла
    при условии, что файл существует и содержит корректные данные.
    Должен вернуть mock_data.
    """
    mock_data = {"user_currencies": ["USD", "EUR"]}
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        assert load_user_settings() == mock_data


def test_load_user_settings_file_not_found():
    """
    Тест для функции load_user_settings.
    Проверяет поведение функции, когда файл настроек пользователя не найден.
    Должен вернуть None.
    """
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert load_user_settings() is None


def test_load_user_settings_json_decode_error():
    """
    Тест для функции load_user_settings.
    Проверяет обработку ошибки некорректного JSON-формата
    в файле настроек пользователя.
    Должен вернуть None.
    """
    with patch("builtins.open", mock_open(read_data="not a json")):
        assert load_user_settings() is None


@patch("requests.get")
def test_get_exchange_rate_success(mock_get):
    """
    Тест для функции get_exchange_rate.
    Проверяет успешное получение курсов валют от API сервиса.
    Моделирует успешный ответ сервера с курсами валют
    и проверяет корректность возвращаемых курсов.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"conversion_rates": {"USD": 1.0, "EUR": 0.85}}
    with patch("src.views.load_user_settings", return_value={"user_currencies": ["USD", "EUR"]}):
        result = get_exchange_rate()
        assert result == {"USD": 1.0, "EUR": 0.85}


@patch("requests.get")
def test_get_exchange_rate_failure(mock_get):
    """
    Тест для функции get_exchange_rate.
    Проверяет обработку ошибки при неуспешном ответе сервера.
    Моделирует ситуацию с ошибочным статусом HTTP и проверяет,
    что функция возвращает None.
    """
    mock_get.return_value.status_code = 404
    with patch("src.views.load_user_settings", return_value={"user_currencies": ["USD"]}):
        result = get_exchange_rate()
        assert result is None


@patch("src.views.TimeSeries")
def test_get_stock_price_success(mock_time_series):
    """
    Тест для функции get_stock_price.
    Проверяет успешное получение цены акции.
    Моделирует успешный ответ API получения котировок и проверяет,
    что возвращаемая цена соответствует ожидаемой.
    """
    mock_ts_instance = mock_time_series.return_value
    mock_ts_instance.get_quote_endpoint.return_value = ({"05. price": "123.45"}, None)

    price = get_stock_price("AAPL")

    assert price == 123.45
    mock_ts_instance.get_quote_endpoint.assert_called_once_with(symbol="AAPL")


@patch("src.views.ALPHA_VANTAGE_API_KEY", None)
def test_get_stock_price_no_api_key():
    """
    Тест для функции get_stock_price.
    Проверяет, что вызывается исключение ValueError, если API ключ отсутствует.
    """
    with pytest.raises(ValueError, match="Необходимо указать API ключ в .env файле."):
        get_stock_price("AAPL")


# Тест для RuntimeError, когда API возвращает ошибку
@patch("src.views.TimeSeries")
def test_get_stock_price_runtime_error(mock_time_series):
    """
    Тестирует функцию get_stock_price на случай возникновения RuntimeError,
    если метод get_quote_endpoint выбрасывает исключение. Проверяет, что
    сообщение об ошибке соответствует ожидаемому.
    """
    mock_ts_instance = mock_time_series.return_value
    mock_ts_instance.get_quote_endpoint.side_effect = Exception("API Error")

    with pytest.raises(RuntimeError, match="Ошибка при получении данных для AAPL: API Error"):
        get_stock_price("AAPL")


def test_get_greeting():
    """
    Тестирует функцию get_greeting с различными входными значениями времени
    и проверяет, что возвращаемое приветствие соответствует времени суток.
    """
    assert get_greeting(6) == "Доброе утро"
    assert get_greeting(13) == "Добрый день"
    assert get_greeting(19) == "Добрый вечер"
    assert get_greeting(23) == "Доброй ночи"
    assert get_greeting(3) == "Доброй ночи"


def test_parse_datetime():
    """
    Тестирует функцию parse_datetime, проверяя, что строка даты и времени
    корректно преобразуется в объект datetime.
    """
    datestr = "12-10-2023 08:45:00"
    expected_datetime = datetime(2023, 10, 12, 8, 45, 0)
    assert parse_datetime(datestr) == expected_datetime


def create_test_excel_file(data):
    """
    Создает временный Excel файл с предоставленными данными для тестов
    и возвращает имя файла.
    """
    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        file_name = tmp.name
        df = pd.DataFrame(data)
        df.to_excel(file_name, index=False)
    return file_name


def create_temp_excel(data, file_path):
    """
    Создает временный Excel файл с заданными данными.
    """
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)


def test_process_excel_data_valid_case():
    """
    Тестирует функцию process_excel_data при наличии валидных данных в Excel,
    проверяя, что результат соответствует ожидаемым данным.
    """
    data = {
        "Дата операции": ["01-09-2023 12:00:00", "15-09-2023 15:30:00", "30-09-2023 10:00:00"],
        "Сумма": [100, 200, 300],
    }

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel_file:
        file_name = tmp_excel_file.name
        create_temp_excel(data, file_name)

    try:
        specific_date = "01.09.2023"
        result = process_excel_data(file_name, specific_date)

        if isinstance(result, str):
            result = json.loads(result)

        expected_data = [
            {"Дата операции": "2023-09-01T12:00:00.000", "Сумма": 100},
            {"Дата операции": "2023-09-15T15:30:00.000", "Сумма": 200},
        ]

        assert result == expected_data
    finally:
        try:
            os.remove(file_name)
        except OSError:
            pass


def test_process_excel_data_no_matching_records():
    """
    Тестирует функцию process_excel_data, проверяя случай, когда в данных
    Excel нет записей, соответствующих заданной дате.
    """
    data = {"Дата операции": ["05-10-2023 12:00:00", "20-10-2023 15:30:00"], "Сумма": [100, 200]}

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel_file:
        file_name = tmp_excel_file.name
        create_temp_excel(data, file_name)

    try:
        specific_date = "01.09.2023"
        result = process_excel_data(file_name, specific_date)

        expected_data = []

        result_data = json.loads(result)

        assert result_data == expected_data

    finally:
        try:
            os.remove(file_name)
        except OSError:
            pass


def test_process_excel_data_invalid_date_format():
    """
    Тестирует обработку данных из Excel-файла с использованием даты в неверном формате.
    Этот тест создает временный Excel-файл с данными, содержащими правильный формат даты,
    однако затем пытается обработать данные, предоставив дату в неверном формате.
    Ожидается, что вызов функции `process_excel_data` с некорректным форматом даты
    вызовет исключение.
    :return:
    """
    data = {"Дата операции": ["05-10-2023 12:00:00"], "Сумма": [100]}

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel_file:
        file_name = tmp_excel_file.name
        create_temp_excel(data, file_name)

    try:
        specific_date = "01/09/2023"  # Invalid format
        with pytest.raises(Exception):
            process_excel_data(file_name, specific_date)
    finally:
        try:
            os.remove(file_name)
        except OSError:
            pass


def test_process_excel_data_invalid_file_path():
    """
    Тестирует обработку данных из Excel-файла с несуществующим путем к файлу.
    Этот тест пытается вызвать функцию `process_excel_data` с именем несуществующего файла.
    Ожидается, что при этом будет вызвано исключение из-за невозможности найти файл.
    :return:
    """
    specific_date = "01-09-2023 00:00:00"
    with pytest.raises(Exception):
        process_excel_data("non_existing_file.xlsx", specific_date)


# Запуск тестов
if __name__ == "__main__":
    pytest.main()
