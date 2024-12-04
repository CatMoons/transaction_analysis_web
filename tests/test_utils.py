import pandas as pd
import pytest
from src.utils import transactions_xlsx, web_search_xcl, num_card_account
from unittest.mock import patch
import json

def test_transactions_xlsx_empty_string():
    '''
    Тест проверяет, что функция transactions_xlsx возвращает пустой список, когда ей передается пустая строка в качестве имени файла.
    '''
    assert transactions_xlsx("") == []

def test_transactions_xlsx_nonexistent_file():
    '''
    Тест проверяет, что функция transactions_xlsx возвращает пустой список, когда передается несуществующее имя файла.
    '''
    assert transactions_xlsx("nonexistent_file.xlsx") == []

def test_transactions_xlsx_valid_file(mocker):
    '''
    Тест проверяет, что функция transactions_xlsx правильно считывает данные из существующего файла Excel.
    Используется mocker для замены функции pandas.read_excel на фиктивные данные.
    '''
    fake_data = [
        {"Категория": "еда", "Сумма": 100},
        {"Категория": "транспорт", "Сумма": 50}
    ]
    mocker.patch('pandas.read_excel', return_value=pd.DataFrame(fake_data))

    result = transactions_xlsx("fake_file.xlsx")
    assert result == fake_data

def test_web_search_xcl_no_matches():
    '''
    Тест проверяет, что функция web_search_xcl возвращает пустой список в формате JSON,
    если в переданных транзакциях нет записей, соответствующих указанной категории.
    '''
    transactions = [
        {"Категория": "еда", "Сумма": 100},
        {"Категория": "транспорт", "Сумма": 50}
    ]
    result = web_search_xcl(transactions, "одежда")
    assert json.loads(result) == []

def test_web_search_xcl_with_matches():
    '''
    Тест проверяет, что функция web_search_xcl возвращает список в формате JSON, содержащий только те транзакции,
    где категория совпадает с указанной (включая учет регистра).
    '''
    transactions = [
        {"Категория": "еда", "Сумма": 100},
        {"Категория": "транспорт", "Сумма": 50},
        {"Категория": "Еда", "Сумма": 200}
    ]
    expected_result = json.dumps([
        {"Категория": "еда", "Сумма": 100},
        {"Категория": "Еда", "Сумма": 200}
    ], ensure_ascii=False)
    assert web_search_xcl(transactions, "еда") == expected_result

def test_num_card_account_single_transaction():
    '''
    Тест проверяет, что функция num_card_account корректно вычисляет сумму операции для одного результата поиска по номеру карты.
    Сумма округляется до целого числа.
    '''
    transactions = [
        {'Номер карты': '*3456', 'Сумма операции с округлением': 150.75}
    ]
    user_input = '*3456'
    result_json = num_card_account(transactions, user_input)
    result = json.loads(result_json)

    assert result['Сумма операций'] == 151

def test_num_card_account_multiple_transactions():
    '''
    Тест проверяет, что функция num_card_account вычисляет корректное общее значение суммы операций,
    когда есть несколько транзакций с одинаковым номером карты.
    '''
    transactions = [
        {'Номер карты': '*3456', 'Сумма операции с округлением': 150.75},
        {'Номер карты': '*3456', 'Сумма операции с округлением': 49.50},
        {'Номер карты': '*7654', 'Сумма операции с округлением': 100.00},
        {'Номер карты': '*3456', 'Сумма операции с округлением': 200.25}
    ]
    user_input = '*3456'
    expected_sum = 400
    result = num_card_account(transactions, user_input)
    assert json.loads(result)["Сумма операций"] == expected_sum

def test_num_card_account_no_transactions():
    '''
    Тест проверяет, что функция num_card_account возвращает нулевую сумму операций,
    если в списке транзакций нет записей с искомым номером карты.
    '''
    transactions = [
        {'Номер карты': '*7654', 'Сумма операции с округлением': 100.00}
    ]
    user_input = '*3456'
    expected_result = '{"Номер карты": "*3456", "Сумма операций": 0}'

    with patch('builtins.input', return_value=user_input):
        assert num_card_account(transactions, user_input) == expected_result

def test_num_card_account_empty_transactions_list():
    '''
    Тест проверяет, что функция num_card_account возвращает нулевую сумму операций,
    если список транзакций пуст.
    '''
    transactions = []
    user_input = '*5091'
    result = num_card_account(transactions, user_input)
    expected_result = '{"Номер карты": "*5091", "Сумма операций": 0}'

    assert result == expected_result