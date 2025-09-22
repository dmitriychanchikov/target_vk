import sys
import time

import __init__
from settings.config import ATTEMPTS, CAPTCHA_TIME, WAIT_TIME
from common_utils.driver import (
    check_and_get_new_url,
    load_website,
    reload_website,
)
from utils.ad import (
    click_cancel_ad,
    click_redact_note,
    click_save_ad,
    find_ad_error,
    find_min_limit_error
)
from utils.note import (
    cancel_save_note,
    find_captcha,
    process_redact_note,
    save_note
)
from utils.task import (
    change_task_name,
    click_redact_ad,
    click_run_task,
    click_stop_task,
    find_run_error,
    get_task_status
)


def pipeline_redact_note(driver, abs_data):
    attempts = 0
    need_reload = False

    while attempts <= ATTEMPTS:
        try:
            if attempts > 0:
                time.sleep(WAIT_TIME)
                if need_reload:
                    if not reload_website(driver):
                        return False
                    need_reload = False
                print(f"Попытка №{attempts} повторного редактирования записи...")

            if not click_redact_note(driver):
                attempts += 1
                need_reload = True
                continue
            if find_ad_error(driver):
                attempts += 1
                need_reload = True
                continue
            print("Окно редактирования записи открыто")

            if not process_redact_note(driver, abs_data):
                attempts += 1
                if not cancel_save_note(driver):
                    need_reload = True
                continue
            print("Запись успешно отредактирована")

            if not save_note(driver):
                attempts += 1
                if not cancel_save_note(driver):
                    need_reload = True
                continue

            if not find_captcha(driver):
                print("Запись успешно сохранена, окно редактирования записи закрыто")
                return True
            
            for i in range(int(CAPTCHA_TIME / WAIT_TIME) + 10):
                if not find_captcha(driver):
                    print("КАПЧА ПРОЙДЕНА!")
                    break
                # TODO: check captcha failure
                if i == int(CAPTCHA_TIME / WAIT_TIME):
                    sys.exit(f"КАПЧА НЕ ПРОЙДЕНА ЗА {CAPTCHA_TIME} СЕКУНД! ВЫХОД ИЗ ПРОГРАММЫ!")
                time.sleep(WAIT_TIME)
            need_reload = True
        
        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось отредактировать запись: {str(e)}")
            attempts += 1
            need_reload = True
    
    print(f"Не удалось отредактировать запись после {ATTEMPTS} попыток")
    return False


def pipeline_redact_ad(driver, abs_data):
    attempts = 0
    need_reload = False

    while attempts <= ATTEMPTS:
        try:
            min_limit_error = False

            if attempts > 0:
                time.sleep(WAIT_TIME)
                if need_reload:
                    if not load_website(driver, abs_data['url']):
                        return False
                    need_reload = False
                print(f"Попытка №{attempts} повторного редактирования объявления...")

            if not click_redact_ad(driver):
                attempts += 1
                need_reload = True
                continue
            redact_url = check_and_get_new_url(driver, abs_data['url'])
            if redact_url == None:
                attempts += 1
                need_reload = True
                continue
            print("Страница редактирования объявления успешно открыта")

            if not pipeline_redact_note(driver, abs_data):
                attempts += 1
                continue
            print("В объявлении обновлена запись")

            if not click_save_ad(driver):
                attempts += 1
                if not click_cancel_ad(driver):
                    need_reload = True
                continue
            if find_min_limit_error(driver):
                min_limit_error = True
                click_cancel_ad(driver)
            url = check_and_get_new_url(driver, redact_url)
            if url != abs_data['url']:
                attempts += 1
                need_reload = True
                continue
            if min_limit_error:
                print("Объявление не сохранено, произошел возврат на исходную страницу")
                return True, min_limit_error
            print("Объявление успешно сохранено, произошел возврат на исходную страницу")
            return True, min_limit_error
        
        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось отредактировать объявление: {str(e)}")
            attempts += 1
            need_reload = True

    print(f"Не удалось отредактировать объявление после {ATTEMPTS} попыток")
    return False, min_limit_error


def pipeline_stop_task(driver, abs_data):
    attempts = 0

    while attempts <= ATTEMPTS:
        try:
            if attempts > 0:
                time.sleep(WAIT_TIME)
                if not load_website(driver, abs_data['url']):
                    return False
                print(f"Попытка №{attempts} повторной остановки задачи...")
            
            task_status = get_task_status(driver)
            if task_status is None:
                attempts += 1
                continue
            if task_status == 'Запущено' or task_status == 'Запускается' or task_status == 'Проверяется':
                if not click_stop_task(driver):
                    attempts += 1
                    continue   
            return True
        
        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось остановить задачу: {str(e)}")
            attempts += 1

    print(f"Не удалось остановить задачу после {ATTEMPTS} попыток")
    return False


def pipeline_run_task(driver, abs_data, set_min_limit_error=False):
    attempts = 0

    while attempts <= ATTEMPTS:
        try:
            if attempts > 0:
                time.sleep(WAIT_TIME)
                if not load_website(driver, abs_data['url']):
                    return False
                print(f"Попытка №{attempts} повторного запуска задачи...")
            
            if set_min_limit_error:
                new_name = abs_data['name'] + ' (маленькая аудитория)'
                if not change_task_name(driver, new_name):
                    attempts += 1
                    continue
                print("Объявление не запущено, задача переименована")
                return True

            if not change_task_name(driver, abs_data['name']):
                attempts += 1
                continue

            task_status = get_task_status(driver)
            if task_status is None:
                attempts += 1
                continue
            if task_status != 'Остановлено':
                if not pipeline_stop_task(driver, abs_data):
                    attempts += 1
                    continue

            if not click_run_task(driver):
                attempts += 1
                continue
        
            if find_run_error(driver):
                new_name = abs_data['name'] + ' +'
                if not change_task_name(driver, new_name):
                    attempts += 1
                    continue
                print("Объявление не запущено, задача переименована")
            else:
                print("Задача успешно запущена")
            return True
        
        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось запустить задачу: {str(e)}")
            attempts += 1

    print(f"Не удалось запустить задачу после {ATTEMPTS} попыток")
    return False


def main_pipeline(driver, abs_data):
    attempts = 0

    while attempts <= ATTEMPTS:
        try:
            if attempts > 0:
                time.sleep(WAIT_TIME)
                print(f"Попытка №{attempts} повторной обработки задачи '{abs_data['name']}'...")

            if not load_website(driver, abs_data['url']):
                attempts += 1
                continue

            if not pipeline_stop_task(driver, abs_data):
                attempts += 1
                continue

            pipeline_redact_ad_statuses = pipeline_redact_ad(driver, abs_data)
            if not pipeline_redact_ad_statuses[0]:
                attempts += 1
                continue

            if not pipeline_run_task(driver, abs_data, pipeline_redact_ad_statuses[1]):
                attempts += 1
                continue
            print(f"Задача '{abs_data['name']}' успешно обработана")
            return True
        
        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось обработать задачу '{abs_data['name']}': {str(e)}")
            attempts += 1

    print(f"Не удалось обработать задачу '{abs_data['name']}' после {ATTEMPTS} попыток")
    return False
