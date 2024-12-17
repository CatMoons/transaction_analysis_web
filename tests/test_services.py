import json
from io import BytesIO

import pandas as pd
import pytest

from src.services import analyze_cashback, get_transactions_with_phones


def test_analyze_cashback():
    """
    Тестирует функцию analyze_cashback, которая анализирует кэшбэк по транзакциям за указанный месяц и год.

    В процессе теста:
    1. Создаются mock данные в виде Excel файла с транзакциями в памяти.
    2. Данные содержат три транзакции с различными категориями и суммами кэшбэка.
    3. Функция analyze_cashback выполняется для анализа августовских транзакций 2023 года.
    4. Проверяется, что результат выполнения функции соответствует ожидаемым значениям.

    Ожидаемый результат:
    {
        "Еда": 75.0,
        "Транспорт": 100.0
    }
    """
    # Создаем mock данные в виде Excel файла в памяти
    data = BytesIO()
    df = pd.DataFrame(
        {
            "Дата операции": ["01.08.2023 12:00:00", "15.08.2023 15:30:00", "22.08.2023 18:45:00"],
            "Категория": ["Еда", "Транспорт", "Еда"],
            "Кэшбэк": [50.0, 100.0, 25.0],
        }
    )
    df.to_excel(data, index=False)
    data.seek(0)  # Переходим в начало файла

    # Выполняем функцию
    result_json = analyze_cashback(data, 2023, 8)
    result = json.loads(result_json)

    # Проверяем результаты
    expected_result = {"Еда": 75.0, "Транспорт": 100.0}
    assert result == expected_result


def test_get_transactions_with_phones():
    """
    Тестирует функцию get_transactions_with_phones, которая извлекает транзакции, содержащие номера телефонов, из описания операций.

    В процессе теста:
    1. Создаются mock данные в виде Excel файла с описаниями транзакций в памяти.
    2. Данные содержат три описания, из которых два включают номера телефонов.
    3. Функция get_transactions_with_phones выполняется для поиска телефонных номеров в описаниях.
    4. Проверяется, что результат выполнения функции соответствует ожидаемым значениям.

    Ожидаемый результат:
    [
        {"index": 0, "description": "Оплата телефона +7 901 234-56-78", "phone_numbers": ["+7 901 234-56-78"]},
        {"index": 2, "description": "Перевод с карты на карту 8 916 123-45-67", "phone_numbers": ["8 916 123-45-67"]},
    ]
    """
    # Создаем mock данные в виде Excel файла в памяти
    data = BytesIO()
    df = pd.DataFrame(
        {
            "Описание": [
                "Оплата телефона +7 901 234-56-78",
                "Покупка в магазине",
                "Перевод с карты на карту 8 916 123-45-67",
            ]
        }
    )
    df.to_excel(data, index=False)
    data.seek(0)  # Переходим в начало файла

    # Выполняем функцию
    result_json = get_transactions_with_phones(data)
    result = json.loads(result_json)

    # Проверяем результаты
    expected_result = [
        {"index": 0, "description": "Оплата телефона +7 901 234-56-78", "phone_numbers": ["+7 901 234-56-78"]},
        {"index": 2, "description": "Перевод с карты на карту 8 916 123-45-67", "phone_numbers": ["8 916 123-45-67"]},
    ]
    assert result == expected_result


if __name__ == "__main__":
    pytest.main()
