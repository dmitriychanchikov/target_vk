import re
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from settings.config import SLEEP_TIME, WAIT_TIME
from utils.common import (
    click_safely,
    insert_value_safely,
    replace_html_safely
)


# Additional functions

def replace_name_in_text(driver, pattern, new_name):
    try:
        post_text_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "wpe_text"))
        )
        current_html = post_text_element.get_attribute('innerHTML')
        updated_html = re.sub(
            pattern.replace('{}', r'[\w-]+'),  # это
            pattern.replace('{}', new_name),   # меняется на это
            current_html
        )
        if not replace_html_safely(driver, post_text_element, updated_html):
            print('Не удалось заменить имя/фамилию в тексте')
            return False
        print(f"Имя/фамилия успешно заменено(а) на '{new_name}'")
        return True
    
    except TimeoutException:
        print("Не удалось найти текстовое поле")
        return False
        
    except Exception as e:
        print(f"Ошибка при замене имени/фамилии: {str(e)}")
        return False
    

def close_photo(driver):
    try:
        close_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ui_thumb_x_button._close_btn"))
        )
        if not click_safely(close_button):
            print("Не удалось нажать на кнопку закрытия фотографии")
            return False
        print("Кнопка закрытия фотографии успешно нажата")
        return True
        
    except TimeoutException:
        print("Не удалось найти кнопку закрытия фотографии")
        return False
    
    except Exception as e:
        print(f"Ошибка при закрытии фотографии: {str(e)}")
        return False
    
def close_link(driver):
    try:
        close_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.page_media_x_wrap.inl_bl"))
        )
        if not click_safely(close_button):
            print("Не удалось нажать на кнопку закрытия ссылки")
            return False
        print("Кнопка закрытия ссылки успешно нажата")
        return True
        
    except TimeoutException:
        print("Не удалось найти кнопку закрытия ссылки")
        return False
    
    except Exception as e:
        print(f"Ошибка при закрытии ссылки: {str(e)}")
        return False
    

def click_add_photo(driver):
    try:
        photo_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ms_item.ms_item_photo._type_photo"))
        )
        if not click_safely(photo_element):
            print("Не удалось нажать кнопку добавления фотографии")
            return False
        print("Кнопка добавления фотографии успешно нажата")
        return True
        
    except TimeoutException:
        print("Не удалось найти кнопку добавления фотографии")
        return False
    
    except Exception as e:
        print(f"Ошибка при нажатии кнопки добавления фотографии: {str(e)}")
        return False

def upload_photo(driver, file_path):
    try:
        file_input = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.file[type='file']"))
        )
        file_input.send_keys(file_path)
        print(f"Фотография '{file_path}' успешно загружена")
        return True
    
    except TimeoutException:
        print("Не удалось найти скрытое поле для загрузки фотографии")
        return False
        
    except Exception as e:
        print(f"Ошибка загрузки фотографии: {str(e)}")
        return False


def refresh_link(driver):
    try:
        post_text_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.ID, "wpe_text"))
        )
        post_text_element.click()
        post_text_element.send_keys(" ", Keys.BACKSPACE)
        print("Ссылка успешно обновлена")
        return True
    
    except TimeoutException:
        print("Не удалось найти текстовое поле")
        return False
    
    except Exception as e:
        print(f"Ошибка обновления ссылки: {str(e)}")
        return False    


def click_add_sign(driver):
    try:
        sign_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.medadd_c_linkimg_controls_btn#medadd_ctrl_upload"))
        )
        if not click_safely(sign_element):
            print("Не удалось нажать кнопку добавления знака")
            return False
        print("Кнопка добавления знака успешно нажата")
        return True
        
    except TimeoutException:
        print("Не удалось найти кнопку добавления знака")
        return False
    
    except Exception as e:
        print(f"Ошибка при нажатии кнопки добавления знака: {str(e)}")
        return False
    
def upload_sign(driver, file_path):
    try:
        file_input = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        file_input.send_keys(file_path)
        print(f"Знак '{file_path}' успешно загружен")
        return True
    
    except TimeoutException:
        print("Не удалось найти скрытое поле для загрузки знака")
        return False
        
    except Exception as e:
        print(f"Ошибка загрузки знкака: {str(e)}")
        return False

def resize_sign(driver):
    try:
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".tag_frame"))
        )
        
        handles = {
            'nw': driver.find_element(By.CSS_SELECTOR, ".tag_frame_handle.nw"),
            'se': driver.find_element(By.CSS_SELECTOR, ".tag_frame_handle.se")
        }
        
        ActionChains(driver)\
            .move_to_element(handles['nw'])\
            .click_and_hold()\
            .move_by_offset(-100, -70)\
            .release()\
            .perform()
            
        time.sleep(SLEEP_TIME)
        
        ActionChains(driver)\
            .move_to_element(handles['se'])\
            .click_and_hold()\
            .move_by_offset(100, 70)\
            .release()\
            .perform()

        print("Размеры знака изменены с двух сторон")
        return True
    
    except TimeoutException:
        print("Не удалось найти элементы для изменения размеров знака")
        return False
        
    except Exception as e:
        print(f"Ошибка при изменении размеров знака: {str(e)}")
        return False

def save_sign(driver):
    try:
        edit_post_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, ".//button[contains(@onclick, 'OwnerPhoto.editDone')]"))
        )
        if not click_safely(edit_post_button):
            print("Не удалось нажать кнопку сохранения знака")
            return False
        print("Знак успешно сохранен")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку сохранения знака")
        return False
        
    except Exception as e:
        print(f"Ошибка сохранения знкака: {str(e)}")
        return False


def change_link_message(driver, message):
    try:
        link_message_element = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "medadd_inline_edit_target"))
        )
        link_message_element.click()
        input_element = WebDriverWait(link_message_element, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "medadd_inline_edit"))
        )
        if not insert_value_safely(driver, input_element, message):
            print("Не удалось изменить название ссылки")
            return False
        print("Название ссылки изменено")
        return True
    
    except TimeoutException:
        print("Не удалось найти название ссылки")
        return False
        
    except Exception as e:
        print(f"Ошибка изменения названия ссылки: {str(e)}")
        return False
    
def delete_link_button(driver):
    try:
        link_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.XPATH, ".//div[contains(@onclick, 'cur.shareRemoveButton')]"))
        )
        if not click_safely(link_button):
            print("Не удалось удалить кнопку в ссылке")
            return False
        print("Кнопка в ссылке удалена")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку в ссылке")
        return False
        
    except Exception as e:
        print(f"Ошибка удаления кнопки в ссылке: {str(e)}")
        return False


def find_note_error(driver):
    try:
        error_area = WebDriverWait(driver, SLEEP_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "wpe_error.error"))
        )
        print(f"Найдена ошибка: '{error_area.text}'")
        return True
    
    except:
        return False


# Main functions

def process_redact_note(driver, ads_data):
    try:
        if len(ads_data['pattern']) > 2:
            if not replace_name_in_text(driver, ads_data['pattern'], ads_data['name']):
                return False

        if not close_photo(driver):
            return False
        if not close_link(driver):
            return False

        if not click_add_photo(driver):
            return False
        if not upload_photo(driver, ads_data['photo_path']):
            return False

        if not refresh_link(driver):
            return False
        time.sleep(SLEEP_TIME)

        if not click_add_sign(driver):
            return False
        if not upload_sign(driver, ads_data['sign_path']):
            return False
        if not resize_sign(driver):
            return False
        if not save_sign(driver):
            return False

        if not change_link_message(driver, ads_data['message']):
            return False
        if not delete_link_button(driver):
            return False
        return True
    
    except Exception as e:
        print(f"Не удалось отредактировать запись: {str(e)}")
        return False


def click_save_note(driver):
    try:
        save_btn = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#wpe_save"))
        )
        if not click_safely(save_btn):
            print("Не удалось нажать кнопку 'Сохранить'")
            return False
        if find_note_error(driver):
            print("Сохранение записи отменено")
            return False
        print("Кнопка 'Сохранить' успешно нажата")
        return True
    
    except TimeoutException:
        print("Не удалось найти кнопку 'Сохранить'")
        return False
        
    except Exception as e:
        print(f"Ошибка при нажатии кнопки 'Сохранить': {str(e)}")
        return False

def click_cancel_note(driver):
    try:
        panel = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CLASS_NAME, "box_controls_buttons.fl_r"))   
        )
        cancel_btn = WebDriverWait(panel, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "FlatButton.FlatButton--tertiary.FlatButton--size-m"))
        )
        if not click_safely(cancel_btn):
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
