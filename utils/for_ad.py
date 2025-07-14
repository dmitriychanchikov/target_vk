from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from settings.config import SLEEP_TIME, WAIT_TIME
from utils.common import click_safely


# Main functions

def click_redact_note(driver):
    try:
        link_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, ".//button[contains(@onclick, 'AdsEdit.showEditingPostBox')]"))
        )
        if not click_safely(link_button):
            print("Не удалось нажать на кнопку 'Редактировать запись'")
            return False
        print("Кнопка 'Редактировать запись' нажата")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку 'Редактировать запись'")
        return False
        
    except Exception as e:
        print(f"Ошибка при нажатии на кнопку 'Редактировать запись': {str(e)}")
        return False


def find_ad_error(driver):
    try:
        error_area = WebDriverWait(driver, SLEEP_TIME).until(
            EC.presence_of_element_located((By.ID, "ads_edit_error_ad"))
        )
        if "unshown" in error_area.get_attribute("class"):
            return False
        print(f"Найдена ошибка: '{error_area.text}'")
        return True
    
    except:
        return False
    
def find_min_limit_error(driver):
    try:
        error_area = WebDriverWait(driver, SLEEP_TIME).until(
            EC.presence_of_element_located((By.ID, "ads_edit_error_targeting"))
        )
        if "unshown" in error_area.get_attribute("class"):
            return False
        print(f"Найдена ошибка: '{error_area.text}'")
        return True
    
    except:
        return False


def click_save_ad(driver):
    try:
        save_btn = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#ads_edit_button_save_ad"))
        )
        if not click_safely(save_btn):
            print("Не удалось нажать кнопку 'Сохранить'")
            return False
        if find_ad_error(driver):
            print("Сохранение объявления отменено")
            return False
        print("Кнопка 'Сохранить' успешно нажата")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку 'Сохранить'")
        return False
        
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Сохранить': {str(e)}")
        return False

def click_cancel_ad(driver):
    try:
        panel = WebDriverWait(driver, WAIT_TIME).until(  
            EC.presence_of_element_located((By.ID, "ads_edit_controls_buttons_row"))   
        )
        cancel_link = WebDriverWait(panel, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.as_button.fl_l[href*='ads?act=office']"))
        )
        if not click_safely(cancel_link):
            print("Не удалось нажать кнопку 'Отмена'")
            return False
        print("Кнопка 'Отмена' успешно нажата")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку 'Отмена'")
        return False
        
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Отмена': {str(e)}")
        return False
