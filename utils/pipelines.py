import sys
import time

from settings.config import ATTEMPTS, CAPTCHA_TIME, WAIT_TIME
from utils.common import (
    check_and_get_new_url,
    load_website,
    reload_website,
)
from utils.for_abs import (
    click_redact_ad,
    click_run_task,
    change_task_name,
    find_run_error
)
from utils.for_ad import (
    click_redact_note,
    click_save_ad,
    click_cancel_ad,
    find_ad_error
)
from utils.for_note import (
    save_note,
    cancel_save_note,
    process_redact_note,
    find_captcha
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
            url = check_and_get_new_url(driver, redact_url)
            if url != abs_data['url']:
                attempts += 1
                need_reload = True
                continue
            print("Объявление успешно сохранено, произошел возврат на исходную страницу")
            return True
        
        except Exception as e:
            if attempts >= ATTEMPTS:
                break
            print(f"Не удалось отредактировать объявление: {str(e)}")
            attempts += 1
            need_reload = True

    print(f"Не удалось отредактировать объявление после {ATTEMPTS} попыток")
    return False


def pipeline_run_task(driver, abs_data):
    attempts = 0

    while attempts <= ATTEMPTS:
        try:
            if attempts > 0:
                time.sleep(WAIT_TIME)
                if not load_website(driver, abs_data['url']):
                    return False
                print(f"Попытка №{attempts} повторного запуска задачи...")

            if not change_task_name(driver, abs_data['name']):
                attempts += 1
                continue

            if not click_run_task(driver):
                attempts += 1
                continue
        
            if find_run_error(driver):
                new_name = abs_data['name'] + ' +'
                change_task_name(driver, new_name)
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

            if not pipeline_redact_ad(driver, abs_data):
                attempts += 1
                continue

            if not pipeline_run_task(driver, abs_data):
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
