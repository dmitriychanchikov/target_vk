import time

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import __init__
from settings.config import SLEEP_TIME, WAIT_TIME


# Browser

def load_webdriver():
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.maximize_window()
        print("Браузер запущен")
        time.sleep(SLEEP_TIME)
        return driver
    except WebDriverException as e:
        print(f"Не удалось запустить браузер: {str(e)}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка при запуске браузера: {str(e)}")
        return None

def load_website(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, WAIT_TIME).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print(f"Страница '{url}' загружена")
        time.sleep(SLEEP_TIME)
        return True
    except TimeoutException:
        print(f"Страница '{url}' не загрузилась за {WAIT_TIME} секунд")
        return True
    except WebDriverException as e:
        print(f"Ошибка при загрузке страницы: {str(e)}")
        return True
    except Exception as e:
        print(f"Неожиданная ошибка при загрузке страницы: {str(e)}")
        return True

def reload_website(driver):
    try:
        driver.refresh()
        WebDriverWait(driver, WAIT_TIME).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print(f"Страница перезагружена")
        time.sleep(SLEEP_TIME)
        return True
    except TimeoutException:
        print(f"Страница не перезагрузилась за {WAIT_TIME} секунд")
        return False
    except WebDriverException as e:
        print(f"Ошибка при загрузке страницы: {str(e)}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при перезагрузке страницы: {str(e)}")
        return False
    
def check_and_get_new_url(driver, url):
    try:
        WebDriverWait(driver, WAIT_TIME).until(
            lambda d: d.current_url != url
        )
        print(f"Загружена новая страница: '{driver.current_url}'")
        return driver.current_url
    except TimeoutException:
        print(f"URL не изменился, новая страница не загрузилась за {WAIT_TIME} секунд")
        return None
    except WebDriverException as e:
        print(f"Ошибка при загрузке страницы: {str(e)}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка при загрузке страницы: {str(e)}")
        return None
    
def shut_webdriver(driver):
    try:
        time.sleep(WAIT_TIME)
        driver.quit()
        print("Браузер закрыт")
        time.sleep(SLEEP_TIME)
        return True
    except WebDriverException as e:
        print(f"Не удалось остановить браузер: {str(e)}")
        return False
    except Exception as e:
        print(f"Неожиданная ошибка при остановке браузера: {str(e)}")
        return False


# Common actions

def click_safely(element):
    try:
        element.click()
        time.sleep(SLEEP_TIME)
        return True
    except Exception as e:
        print(f"Ошибка клика по элементу: {str(e)}")
        return False

def insert_value_safely(driver, element, value):
    try:
        driver.execute_script(f"arguments[0].value = `{value}`;", element)
        element.send_keys(" ", Keys.BACKSPACE)
        return True
    except Exception as e:
        print(f"Ошибка вставки значения: {str(e)}")
        return False
    
def replace_html_safely(driver, element, new_html):
    try:
        driver.execute_script(f"arguments[0].innerHTML = `{new_html}`;", element)
        driver.execute_script("""
            var event = new Event('input', { bubbles: true });
            arguments[0].dispatchEvent(event);
        """, element)
        return True
    except Exception as e:
        print(f"Ошибка замены текста: {str(e)}")
        return False

def press_escape(driver):
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(SLEEP_TIME)
        return True
    except Exception as e:
        print(f"Ошибка при нажатии клавиши ESCAPE: {str(e)}")
        return False

def click_by_coordinates(driver, x, y):
    try:
        actions = ActionChains(driver)
        actions.move_by_offset(x, y).click().perform()
        actions.move_by_offset(-x, -y).perform()
        time.sleep(SLEEP_TIME)
        return True
    except Exception as e:
        print(f"Ошибка при клике по координатам ({x}, {y}): {str(e)}")
        return False
