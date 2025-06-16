from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from settings.config import SLEEP_TIME, WAIT_TIME
from utils.common import (
    click_safely,
    insert_value_safely
)


def click_redact_ad(driver):
    try:
        edit_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, ".//button[contains(@onclick, 'Ads.disablePreviewButtons')]"))
        )
        if not click_safely(edit_button):
            print("Не удалось нажать на кнопку 'Редактировать'")
            return False
        print("Кнопка 'Редактировать' нажата")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку 'Редактировать'")
        return False
        
    except Exception as e:
        print(f"Ошибка при нажатии на кнопку 'Редактировать': {str(e)}")
        return False


def change_task_name(driver, name):
    try:
        name_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, "//h2[contains(@class, 'ads_union_title_editable')]"))
        )
        name_element.click()
        input_element = WebDriverWait(name_element, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, "//textarea[contains(@class, 'vkuiUnstyledTextField__host')]"))
        )
        if not insert_value_safely(driver, input_element, name):
            input_element.send_keys(Keys.RETURN)
            print("Не удалось изменить имя задачи")
            return False
        input_element.send_keys(Keys.RETURN)
        print(f"Имя задачи изменено на '{name}'")
        return True
    
    except TimeoutException:
        print("Не удалось найти имя задачи")
        return False
        
    except Exception as e:
        print(f"Ошибка изменения имени задачи: {str(e)}")
        return False

def click_run_task(driver):
    try:
        run_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[contains(@onclick, 'Ads.changeStatus') and contains(text(), 'Запустить')]"))
        )
        if not click_safely(run_button):
            print("Не удалось нажать кнопку 'Запустить'")
            return False
        print("Кнопка 'Запустить' успешно нажата")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку 'Запустить'")
        return False
        
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Запустить': {str(e)}")
        return False
