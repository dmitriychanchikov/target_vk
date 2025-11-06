import os
import time
from typing import List, Optional, Tuple
from dotenv import load_dotenv

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, 
    StaleElementReferenceException,
    TimeoutException, 
    WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import __init__
from settings.config import *
from common_utils.driver import *
from utils.db import *


load_dotenv('env/.env')
CABINET = os.getenv('CABINET')


def login(driver, email, password):
    attempts = 0
    
    while attempts <= ATTEMPTS:
        try:
            time.sleep(WAIT_TIME * attempts)
            if attempts > 0:
                print(f"Попытка №{attempts} повторной авторизации")

            login_button = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-bs-target='#loginpopup']"))
            )
            if not click_safely(login_button):
                print(f"Не удалось нажать кнопку 'Войти'")
                attempts += 1
                continue

            email_input = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='modal-content']//form[@class='login-form']//input[@name='email']")
                )
            )
            if not insert_value_safely(driver, email_input, email):
                print(f"Не удалось ввести Email")
                attempts += 1
                continue

            password_input = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='modal-content']//form[@class='login-form']//input[@name='password']")
                )
            )
            if not insert_value_safely(driver, password_input, password):
                print(f"Не удалось ввести Password")
                attempts += 1
                continue

            submit_button = WebDriverWait(driver, WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.login-form-button"))
            )
            if not click_safely(submit_button):
                print(f"Не удалось отправить форму авторизации")
                attempts += 1
                continue
            
            print(f"Пользователь '{email}' успешно авторизован")
            time.sleep(SLEEP_TIME)
            return True

        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось авторизоваться: {str(e)}")
            attempts += 1

    print(f"Не удалось авторизоваться после {ATTEMPTS} попыток")
    return False

def choose_project(driver, project):
    attempts = 0
    
    while attempts <= ATTEMPTS:
        try:
            time.sleep(WAIT_TIME * attempts)
            if attempts > 0:
                print(f"Попытка №{attempts} повторного выбора проекта")

            project_button = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button.header_project_list'))
            )
            current_project = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'active_project'))
            )
            
            if project not in current_project.text:
                click_safely(project_button)
                
                dropdown_menu = WebDriverWait(driver, WAIT_TIME).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'ul.project-list'))
                )
                target_project = dropdown_menu.find_element(By.XPATH, f".//a[contains(., '{project}')]")
                click_safely(target_project)
                print(f"Проект '{project}' успешно выбран")
            else:
                print(f"Проект '{project}' уже выбран")
            return True

        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось выбрать проект: {str(e)}")
            attempts += 1

    print(f"Не удалось выбрать проект после {ATTEMPTS} попыток")
    return False


def prepare_task_creation(driver):
    try:
        first_task = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "history2-one-task"))
        )
        params_button = WebDriverWait(first_task, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'i.si-equalizer.history2-toolbar-items'))
        )
        click_safely(params_button)
        print("Окно параметров задачи успешно открыто")
        return True
    
    except Exception as e:
        print(f"Ошибка при открытии окна параметров задачи: {str(e)}")
        
    return False

def create_task_by_name(driver, name):
    try:
        textarea = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='none_none_array_query-recreate']"))
        )
        insert_value_safely(driver, textarea, name)
        
        name_input = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='modal-content']//input[@name='custom_name']"))
        )
        insert_value_safely(driver, name_input, name)
        
        create_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.task-recreate-button"))
        )
        click_safely(create_button)
        print(f"Задача '{name}' успешно создана")
        return True
        
    except Exception as e:
        print(f"Ошибка при создании задачи '{name}': {str(e)}")
        
    return False


def click_tasks_history(driver):
    try:
        history_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "history2-task-load-more-button"))
        )
        if click_safely(history_button):
            return True
        return False
    except TimeoutException:
        return False

def find_task_by_name(driver, name):
    try:
        task_name_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, f".//div[@class='history2-name'][normalize-space()='{name}']"))
        )
        if task_name_element is None:
            return None, None, 'not_found'
        
        task_element = task_name_element.find_element(By.XPATH, "./ancestor::div[@class='history2-one-task']")
        if task_element is None:
            return None, task_name_element, 'not_found'
        
        task_error_elements = task_element.find_elements(By.XPATH, ".//div[@class='history2-error-row']")
        if any([task_error_element.text for task_error_element in task_error_elements]):
            return task_element, task_name_element, 'stopped'
        
        try:
            task_description_element = task_element.find_element(By.XPATH, ".//div[@class='task-description']")
        except NoSuchElementException:
            task_description_element = None
        if task_description_element is not None:
            return task_element, task_name_element, 'running'
        
        task_name_element = task_element.find_element(By.XPATH, f"//div[@class='history2-name']/a[text()='{name}']")
        return task_element, task_name_element, 'found'
    
    except (TimeoutException, NoSuchElementException):
        return None, None, 'not_found'

def restart_task_by_name(driver, name):
    try:
        task_name_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, f".//div[@class='history2-name'][normalize-space()='{name}']"))
        )
        task_element = task_name_element.find_element(By.XPATH, "./ancestor::div[@class='history2-one-task']")
        task_restart_button = task_element.find_element(By.XPATH, ".//i[@class='si si-reload history2-toolbar-items']")
        click_safely(task_restart_button)
        
        confirm_block = WebDriverWait(driver, WAIT_TIME).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.task2-confirmation-block"))
        )
        confirm_button = WebDriverWait(confirm_block, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.task2-confirmation-button-confirm"))
        )
        click_safely(confirm_button)
        
        return True
    
    except (TimeoutException, NoSuchElementException):
        return False

def get_task_count(task_element):
    try:
        count_element = WebDriverWait(task_element, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, ".//div[i[contains(@class, 'si-docs')]]"))
        )
        return int(count_element.text.replace(" ", ""))
    except (NoSuchElementException, StaleElementReferenceException, TimeoutException, ValueError):
        return None


def fill_search(driver, value):
    try:
        search_input = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "form-control.history-search-input"))
        )
        if not insert_value_safely(driver, search_input, value):
            return False
        time.sleep(SLEEP_TIME)
        return True
    except TimeoutException:
        return False
    

def get_cabinet_number(text, base_part=CABINET):
    if text == base_part:
        return 0
    num_part = text.replace(base_part, "").strip()
    if num_part:
        try:
            return int(num_part)
        except ValueError:
            return float('inf')
    return float('inf')

def get_sorted_cabinets(driver, selector):
    try:
        cabinets_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, selector))
        )
        
        all_cabinet_buttons = WebDriverWait(cabinets_element, WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "th-block.th-audience-block-picker"))
        )
        
        cabinets_with_text = []
        for btn in all_cabinet_buttons:
            try:
                text = btn.text.strip()
                cabinets_with_text.append((btn, text))
            except StaleElementReferenceException:
                continue
        
        return sorted(
            cabinets_with_text,
            key=lambda x: get_cabinet_number(x[1])
        )
        
    except Exception as e:
        print(f"Ошибка при получении списка кабинетов: {str(e)}")
    
    return []

def get_and_choose_cabinets(
    driver,
    cabinets_type: str,          # 'old' | 'new'
    cabinets_mode: str = 'any',  # 'any' | 'only' | 'except'
    cabinets: Optional[List[str]] = None
) -> Optional[List[Tuple[object, str]]]:
    """
    Возвращает список кабинетов (WebElement, text) по типу и режиму фильтрации.

    Примеры:
      - cabinets_mode='only',   cabinets=['Полина 1','Полина 2']   -> брать только эти
      - cabinets_mode='except', cabinets=['Полина 6','Полина 1']   -> брать любые, кроме этих
      - cabinets_mode='any',    cabinets=None/[]                   -> брать любые
    """
    try:
        # Валидация входных параметров
        allowed_types = {'old', 'new'}
        if cabinets_type not in allowed_types:
            raise ValueError(f"Некорректный cabinets_type='{cabinets_type}'. Допустимо: {allowed_types}")

        allowed_modes = {'any', 'only', 'except'}
        if cabinets_mode not in allowed_modes:
            raise ValueError(f"Некорректный mode='{cabinets_mode}'. Допустимо: {allowed_modes}")

        # Сопоставление типа с селектором (проверь реальные значения)
        type_selector = {
            'old': "task-view-save-vk",
            'new': "task-view-save-mytarget",
        }[cabinets_type]

        # Загружаем исходный список
        all_cabinets = get_sorted_cabinets(driver, type_selector)  # List[Tuple[element, text]]
        if not all_cabinets:
            print(f"Кабинеты не найдены [{cabinets_type}]")
            return None
        print(f"Найдены кабинеты [{cabinets_type}]: {[t for _, t in all_cabinets]}")

        # Нормализуем входной список
        cabinets = cabinets or []
        cabinet_set = set(cabinets)

        if cabinets_mode == 'any':
            filtered = all_cabinets

        elif cabinets_mode == 'only':
            if not cabinet_set:
                print("Режим 'only' задан без списка — ничего не выбрано")
                return None
            filtered = [item for item in all_cabinets if item[1] in cabinet_set]

        elif cabinets_mode == 'except':
            if not cabinet_set:
                filtered = all_cabinets  # Пустой список исключений = эквивалент any
            else:
                filtered = [item for item in all_cabinets if item[1] not in cabinet_set]

        if not filtered:
            if cabinets_mode == 'only':
                print(f"Ни один из указанных кабинетов не найден")
            else:
                print(f"После фильтрации не осталось кабинетов")
            return None

        print(f"Выбраны кабинеты [{cabinets_type}][{cabinets_mode}]: {[t for _, t in filtered]}")
        return filtered

    except Exception as e:
        print(f"Ошибка при выборе кабинетов: {str(e)}")
        return None

def check_audience_limit(driver):
    try:
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Достигнут лимит аудиторий.')]"))
        )
        return True
    except TimeoutException:
        return False
    

def check_error(driver):
    try:
        element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='audience-create-content']"))
        )
        if element is not None and element.text != "":
            return True
        return False
    except TimeoutException:
        return False


def check_task_by_name(driver, name, db_path, retry_stopped=True):
    try:        
        task_element, task_name_element, task_status = find_task_by_name(driver, name)
        if task_status == 'not_found':
            print(f"Задача '{name}' не найдена")
            update_value_in_db(db_path, name, 'search_status', 'not_found')
            return None, None, None
        
        if task_status == 'stopped':
            print(f"Задача '{name}' остановлена, требуется перезапуск")
            update_value_in_db(db_path, name, 'search_status', 'stopped')

            if not restart_task_by_name(driver, name):
                print(f"Не удалось перезапустить задачу '{name}'")
                return task_element, task_name_element, None
            print(f"Задача '{name}' перезапущена")

            if retry_stopped:
                task_element, task_name_element, task_count = check_task_by_name(driver, name, db_path, retry_stopped=False)
            return task_element, task_name_element, None

        if task_status == 'running':
            print(f"Задача '{name}' еще не обработана")
            update_value_in_db(db_path, name, 'search_status', 'running')
            return task_element, task_name_element, None

        task_count = get_task_count(task_element)
        if task_count is None:
            print(f"Не удалось получить количество аккаунтов '{name}'")
            return task_element, task_name_element, None
        
        print (f"Задача '{name}' проверена, количество аккаунтов: {task_count}")
        update_value_in_db(db_path, name, 'search_status', 'found')
        return task_element, task_name_element, task_count
    
    except Exception as e:
        print(f"Не удалось проверить задачу '{name}': {str(e)}")
        update_value_in_db(db_path, name, 'search_status', 'not_found')
        return None, None, None


def find_first_task(driver):
    try:
        task_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, f"history2-one-task"))
        )
        if task_element is None:
            return None, None
        
        task_name_element = task_element.find_element(By.CLASS_NAME, "link-primary")
        if task_element is None:
            return task_element, None
        
        return task_element, task_name_element
    
    except (TimeoutException, NoSuchElementException):
        return None, None
    
def add_audience_in_cabinet(driver, name):
    attempts = 0

    while attempts <= ATTEMPTS:
        try:
            time.sleep(WAIT_TIME * attempts)
            if attempts > 0:
                print(f"Попытка №{attempts} повторного создания аудитории в кабинете")

            audience_input = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, "//input[@class='form-control' and contains(@name, 'audience-name')]"))
            )
            if len(name) <= 2:
                name = f'({name})'
            if not insert_value_safely(driver, audience_input, name):
                print(f"Не удалось вставить значение '{name}' в поле 'Название новой аудитории...'")
                attempts += 1
                continue

            audience_button = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, ".//button[contains(@onclick, 'audience') and contains(@onclick, 'create')]"))
            )
            if not click_safely(audience_button):
                print(f"Не удалось нажать кнопку 'Создать' аудиторию")
                attempts += 1
                continue
            
            print(f"Аудитория '{name}' создана в кабинете (предварительно)")
            return True
        
        except TimeoutException:
            print(f"Не удалось создать аудиторию '{name}' в кабинете")
            attempts += 1

    print (f"Не удалось создать аудиторию '{name}' в кабинете после {ATTEMPTS} попыток")
    return False

def save_audience_in_cabinet(driver, name):
    attempts = 0

    while attempts <= ATTEMPTS:
        try:
            audience_block = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, f"//div[contains(@style, 'border-bottom')]"))
            )
            if name not in audience_block.text:
                print(f"Не удалось найти аудиторию '{name}' в кабинете")
                return False
            audience_button = audience_block.find_element(
                By.XPATH, ".//button[contains(@onclick, 'save')] | .//div[contains(@class, 'save-button')]"
            )
            if not click_safely(audience_button):
                print(f"Не удалось нажать кнопку 'Сохранить' аудиторию")
                attempts += 1
                continue
            
            save_message = WebDriverWait(audience_block, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Сохранено')]"))
            )
            if save_message is None:
                print(f"Не получено сообщение 'Сохранено'")
                attempts += 1
                continue
            
            print(f"Получено сообщение 'Сохранено'")
            return True
            
        except TimeoutException:
            print(f"Не удалось сохранить аудиторию '{name}' в кабинете")
            attempts += 1

    print (f"Не удалось сохранить аудиторию '{name}' в кабинете после {ATTEMPTS} попыток")
    return False

def get_names_to_save(db_path):
    names_to_save = []
    
    try:
        names_in_range = get_names_from_db_by_status(db_path, 'count_status', include_values=['in_range'])
        all_names_to_save = get_names_from_db_by_status(db_path, 'save_status', include_values=[None, False])
        for name in all_names_to_save:
            if name in names_in_range:
                names_to_save.append(name)
    
    except Exception as e:
        print(f"Не удалось получить имена для сохранения: {e}")
    
    return names_to_save
