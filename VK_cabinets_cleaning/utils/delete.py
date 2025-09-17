from datetime import datetime, timedelta
from dateutil import parser

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import __init__
from settings.config import *
from common_utils.driver import *


months = {
    'янв': 'Jan', 'фев': 'Feb', 'мар': 'Mar', 'апр': 'Apr',
    'мая': 'May', 'июн': 'Jun', 'июл': 'Jul', 'авг': 'Aug',
    'сен': 'Sep', 'окт': 'Oct', 'ноя': 'Nov', 'дек': 'Dec'
}

def parse_date(date_str):
    try:
        if date_str == '—':
            parsed_date = datetime(1970, 1, 1).date()

        elif 'сегодня' in date_str:
            parsed_date = datetime.now().date()

        elif 'вчера' in date_str:
            parsed_date = datetime.now().date() - timedelta(days=1)

        else:
            if ' в ' in date_str:  # Формат '15 мая в 19:17'
                current_year = datetime.now().year
                date_str = f"{date_str.split(' в ')[0]} {current_year}"  # Добавляем текущий год

            for ru_month, en_month in months.items():
                if ru_month in date_str:
                    date_str = date_str.replace(ru_month, en_month)
                    break
                
            parsed_date = parser.parse(date_str, dayfirst=True).date()

        return parsed_date
    
    except Exception as e:
        print(f"Не удалось распарсить дату: '{date_str}'. Ошибка: {str(e)}")
        return None


def find_error(driver):
    try:
        error_window = WebDriverWait(driver, WAIT_TIME * 0.2).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='box_layout']"))
        )
        if 'Ошибка' not in error_window.text:
            return False
        close_button = WebDriverWait(error_window, WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, ".//span[text()='Закрыть']"))
        )
        click_safely(close_button)
        return True
    
    except (TimeoutException, Exception):
        return False


def pipeline(driver, name, current_date_f, deleted, not_found, with_error, i):
    while True:
        try:
            search_input = WebDriverWait(driver, WAIT_TIME).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@class='ui_search_field _field']"))
            )
            insert_value_safely(driver, search_input, name)
            time.sleep(SLEEP_TIME * 0.5)

            auditory_poles = WebDriverWait(driver, WAIT_TIME * 0.5).until(
                EC.presence_of_all_elements_located((By.XPATH, f".//tr[contains(@class, 'ui_table_row')]"))
            )

            is_found, is_deleted = False, False
            for auditory_pole in auditory_poles[1:21]:
                if len(auditory_pole.text) == 0:
                    continue

                auditory_element = auditory_pole.find_element(By.XPATH, ".//a[@class='ads_retargeting_group_actions_link']")
                if auditory_element.text != name:
                    continue

                auditory_date = auditory_pole.find_element(By.XPATH, ".//span[@class='ads_retargeting_group_wip']")
                date_f = parse_date(auditory_date.text)
                delta = (current_date_f - date_f).days
                if delta < 0:
                    continue

                is_found = True
                click_safely(auditory_element)

                auditory_functions_element = WebDriverWait(driver, WAIT_TIME).until(
                    EC.element_to_be_clickable((By.XPATH, f".//div[@class='dd_menu_rows2']"))
                )
                auditory_delete_button = WebDriverWait(auditory_functions_element, WAIT_TIME).until(
                    EC.element_to_be_clickable((By.XPATH, ".//a[text()='Удалить']"))
                )
                auditory_delete_button.click()
                time.sleep(SLEEP_TIME * 0.5)

                confirm_window = WebDriverWait(driver, WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@class='box_layout']"))
                )
                yes_button = WebDriverWait(confirm_window, WAIT_TIME).until(
                    EC.element_to_be_clickable((By.XPATH, ".//span[text()='Да']"))
                )
                click_safely(yes_button)

                if find_error(driver):
                    with_error.append(name)
                    print(i, name, date_f, 'Ошибка')
                    continue

                deleted.append(name)
                is_deleted = True
                print(i, name, date_f, 'Удалено')
                break
            
            if not is_found:
                if name not in deleted:
                    not_found.append(name)
                    print(i, name, 'Не найдено')

            if not is_deleted:
                break
        
        except (TimeoutException, Exception):
            not_found.append(name)
            print(i, name, 'Не найдено')
            continue
