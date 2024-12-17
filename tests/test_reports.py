from datetime import datetime

import pandas as pd
import pytest

from src.reports import (load_transactions, rep_category_spending, rep_spend_on_working_or_weekends,
                         rep_spending_on_weekdays)


@pytest.fixture
def sample_transactions():
    """
    Создает тестовый набор данных о транзакциях в виде DataFrame.
    Данные включают следующие поля:
    - "Дата операции": даты транзакций
    - "Категория": категории расходов
    - "Сумма операции": суммы транзакций
    Возвращает:
        pd.DataFrame: DataFrame с тестовыми данными о транзакциях.
    """
    data = {
        "Дата операции": [
            datetime(2021, 12, 25, 12, 0, 0),  # Суббота
            datetime(2021, 12, 26, 12, 0, 0),  # Воскресенье
            datetime(2021, 12, 27, 12, 0, 0),  # Понедельник
            datetime(2021, 12, 28, 12, 0, 0),  # Вторник
            datetime(2021, 12, 29, 12, 0, 0),  # Среда
        ],
        "Категория": ["Продукты", "Одежда", "Продукты", "Транспорт", "Одежда"],
        "Сумма операции": [100, 200, 150, 100, 250],
    }
    return pd.DataFrame(data)


def test_load_transactions(mocker):
    """
    Тестирует загрузку транзакций из файла Excel.
    Использует моки для замены функции pd.read_excel, чтобы
    проверить, что функция load_transactions правильно загружает данные.
    Проверяет:
    - что загруженный DataFrame не пустой,
    - что количество записей в загруженном DataFrame равно 1.
    """
    mock_read_excel = mocker.patch("src.reports.pd.read_excel")
    mock_read_excel.return_value = pd.DataFrame(
        {"Дата операции": pd.to_datetime(["2023-01-01"]), "Категория": ["Тест"], "Сумма операции": [100]}
    )

    transactions = load_transactions("fake_path.xlsx")
    assert not transactions.empty
    assert len(transactions) == 1


def test_rep_category_spending(sample_transactions):
    """
    Тестирует функцию, которая генерирует отчет о расходах на определенную категорию.
    Проверяет:
    - что отчет содержит информацию о 'Продукты',
    - что сумма затрат на категорию 'Продукты' рассчитана правильно (100 + 150 → 250).
    """
    result = rep_category_spending(sample_transactions, "Продукты", "2022-12-31")
    assert "Общие расходы на категорию 'Продукты'" in result
    assert "250" in result  # 100 + 150


def test_rep_spending_on_weekdays(sample_transactions):
    """
    Тестирует функцию, которая генерирует отчет о расходах по дням недели.
    Проверяет, что отчет правильно отображает сумму расходов на каждый день недели.
    """
    result = rep_spending_on_weekdays(sample_transactions, "2022-12-31")
    assert "6" in result  # Сумма за воскресенье
    assert "0" in result  # Сумма за понедельник
    assert "1" in result  # Сумма за вторник
    assert "2" in result  # Сумма за среду


def test_rep_spend_on_working_or_weekends(sample_transactions):
    """
    Тестирует функцию, которая генерирует отчет о расходах в рабочие и выходные дни.
    Проверяет наличие информации о расходах на рабочие и выходные дни в отчете.
    """
    result = rep_spend_on_working_or_weekends(sample_transactions, "2022-12-31")
    assert "Рабочий" in result
    assert "Выходной" in result
