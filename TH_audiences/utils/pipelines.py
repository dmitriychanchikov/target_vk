import os
from dotenv import load_dotenv

import __init__
from settings.config import *
from common_utils.driver import *
from utils.db import *
from utils.functions import *


load_dotenv('settings/.env')
URL = os.getenv('URL')
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
PROJECT = os.getenv('PROJECT')
CABINET = os.getenv('CABINET')


def pipeline_browser_preparing():
    try:
        print("Подготовка браузера")
        driver = load_webdriver()
        load_website(driver, URL)
        login(driver, EMAIL, PASSWORD)
        choose_project(driver, PROJECT)
        if driver.current_url != URL:
            load_website(driver, URL)
        return driver
    
    except Exception as e:
        print(f"Ошибка при подготовке браузера: {str(e)}")
        return None

def load_additional_tabs(driver, additional_tabs=[]):
    try:
        if isinstance(additional_tabs, list) and len(additional_tabs) > 0:
            for tab_url in additional_tabs:
                open_new_tab(driver)
                switch_to_tab(driver, -1)
                load_website(driver, tab_url)
            switch_to_tab(driver, 0)
            return driver
    except Exception as e:
        print(f"Ошибка при открытии дополнительных вкладок: {str(e)}")
        return None


def prepare_run_dir(dir):
    print('Подготовка директории запуска')

    if os.path.exists(dir) and os.path.isdir(dir):
        print(f'Директория {dir} уже существует')
    else:
        os.makedirs(dir, exist_ok=True)
        print(f'Создана директория {dir}')

def prepare_input_dir(input_dir, input_data_path):
    print('Подготовка входной директории')

    if os.path.exists(input_dir) and os.path.isdir(input_dir):
        print(f'Директория {input_dir} уже существует')
    else:
        os.makedirs(input_dir, exist_ok=True)
        print(f'Создана директория {input_dir}')

    if os.path.exists(input_data_path):
        print(f'Файл {input_data_path} уже существует')
    else:
        try:
            dir = os.path.dirname(input_dir)
            start, end = os.path.basename(dir).split('_')
            length = int(end) - int(start) + 1
        except Exception:
            length = 1000
        empty_df = pd.DataFrame([""] * length, columns=["Name"])
        empty_df.to_excel(input_data_path, index=False, header=False)
        print(f'Создан пустой файл {input_data_path} на {length} строк')


def inspect_data(
        input_path, 
        search_single_or_equal_chars=True, 
        search_surnames_with_yo=True,
        search_female_surnames=False,
        search_male_surnames=False
    ):
    print('Анализ данных')
    df = load_data(input_path)
    df[0] = df[0].astype(str).str.strip()

    to_delete = {}

    # --- 1. Слова с одинаковыми буквами (регистр игнорируется) ---
    if search_single_or_equal_chars:
        def is_all_same_chars(s):
            s_clean = s.strip()
            return len(s_clean) > 0 and all(ch.lower() == s_clean[0].lower() for ch in s_clean)
        
        single_equal_words = df[df[0].apply(is_all_same_chars)][0].tolist()
        to_delete['single_or_equal_chars'] = single_equal_words

        print("\n🔹 Записи из одинаковых символов:")
        for w in single_equal_words:
            print(w)

    # --- 2. Фамилии с "ё", если есть вариант с "е" ---
    if search_surnames_with_yo:
        yo_words = []
        all_names = set(df[0])
        for name in all_names:
            if 'ё' in name.lower():
                variant = name.replace('ё', 'е').replace('Ё', 'Е')
                if variant in all_names:
                    yo_words.append(name)
        to_delete['surnames_with_yo'] = yo_words

        print("\n🔹 Записи с 'ё', если есть вариант с 'е':")
        for w in yo_words:
            print(w)

    # --- 3. Женские фамилии (окончание на "ва" или "на") ---
    if search_female_surnames:
        female_endings = df[
            df[0].str.lower().str.endswith(('ева', 'ова', 'ина'))
        ][0].tolist()
        to_delete['female_surnames'] = female_endings

        print("\n🔹 Женские фамилии (на '-ева', '-ова', '-ина'):")
        for w in female_endings:
            print(w)

    # --- 4. Мужские фамилии (окончание на "ов", "ев", "ин") ---
    if search_male_surnames:
        male_endings = df[
            df[0].str.lower().str.endswith(('ев', 'ов', 'ин'))
        ][0].tolist()
        to_delete['male_surnames'] = male_endings

        print("\n🔹 Мужские фамилии (на '-ев', '-ов', '-ин'):")
        for w in male_endings:
            print(w)

    print()
    return to_delete

def clean_data(input_path, data_path, to_delete):
    print('Очистка данных')
    df = load_data(input_path)
    df[0] = df[0].astype(str).str.strip()

    # --- Определяем список для удаления ---
    if isinstance(to_delete, dict):
        # собираем все списки в один
        flat_delete = []
        for key, value in to_delete.items():
            if isinstance(value, (list, tuple, set)):
                flat_delete.extend(value)
        to_delete_list = list(set(flat_delete))  # уберем дубликаты
    elif isinstance(to_delete, (list, tuple, set)):
        to_delete_list = list(set(to_delete))
    else:
        raise TypeError("Аргумент 'to_delete' должен быть списком или словарем")

    # --- Удаляем строки ---
    before_count = len(df)
    df = df[~df[0].isin(to_delete_list)]
    after_count = len(df)
    removed_count = before_count - after_count

    print(f'Удалено {removed_count} строк, осталось {after_count} строк')

    # --- Сохраняем результат ---
    df.to_excel(data_path, index=False, header=False)
    print(f'Очищенные данные сохранены в файл {data_path}')


def pipeline_db_preparing(data_path, db_path):
    try:
        print("Подготовка базы данных")
        df = load_data(data_path)
        init_db(db_path)
        insert_names_from_df_to_db(db_path, df)
        return db_path
    except Exception as e:
        print(f"Ошибка при подготовке базы данных: {str(e)}")
        return None


def pipeline_tasks_creating(driver, db_path, need_reload=True):
    created = 0
    
    try:
        if need_reload:
            load_website(driver, URL)
            
        prepare_task_creation(driver)

        names_to_create = get_names_from_db_by_status(db_path, 'create_status', include_values=[None, False])
        found_names = get_names_from_db_by_status(db_path, 'search_status', exclude_values=[None, 'not_found'])

        for name in names_to_create:
            if name in found_names:
                continue
            if create_task_by_name(driver, name):
                update_value_in_db(db_path, name, 'create_status', True)
                created += 1
                if created % 10 == 0:
                    print(f"Создано {created} задач")
            else:
                update_value_in_db(db_path, name, 'create_status', False)
        
        print(f"Всего создано {created} задач")
    
    except Exception as e:
        print(f"Ошибка в пайплайне создания задач: {str(e)}")
        
    return created


def pipeline_tasks_checking(driver, db_path, count_min, count_max, need_reload=True):
    checked = 0

    try:
        names_to_check = get_names_from_db_by_status(db_path, 'count_status', include_values=[None])

        if need_reload:
            load_website(driver, URL)
            
        scrolls = 0
        while scrolls < ATTEMPTS * 20:
            _, _, is_first_name_found = find_task_by_name(driver, names_to_check[0])
            if is_first_name_found == 'not_found':
                click_tasks_history(driver)
                scrolls += 1
                continue
            break
        else:
            print("Первая задача из списка не найдена")
            # _, _, is_second_name_found = find_task_by_name(driver, names_to_check[0])
            # if is_second_name_found == 'not_found':
            #     print("Первая задача из списка не найдена")
            return False
                
        for name in names_to_check:
            print()
            _, _, task_count = check_task_by_name(driver, name, db_path)

            if task_count is None:
                continue
            update_value_in_db(db_path, name, 'accounts_count', task_count)

            if task_count < count_min:
                update_value_in_db(db_path, name, 'count_status', 'too_few')
            elif task_count > count_max:
                update_value_in_db(db_path, name, 'count_status', 'too_many')
            else:
                update_value_in_db(db_path, name, 'count_status', 'in_range')
                checked += 1
                if checked % 10 == 0:
                    print(f"Найдено {checked} задач с числом аккаунтов от {count_min} до {count_max}")
        
        print(f"Всего найдено {checked} задач с числом аккаунтов от {count_min} до {count_max}")
    
    except Exception as e:
        print(f"Ошибка в пайплайне проверки задач: {str(e)}")
        
    return checked


def chunk_pipeline_tasks_adding_and_saving(driver, db_path, cabinets_type, cabinets_mode, cabinets, current_cabinet, need_reload=True):
    added_and_saved = 0
    cabinet_is_changed = False

    try:
        if need_reload:
            load_website(driver, URL)
        else:
            click_by_coordinates(driver, 100, 150)
            press_escape(driver)

        names_to_save = get_names_to_save(db_path)
        if not fill_search(driver, names_to_save[0]):
            print("Не удалось выполнить поиск задач")
            return added_and_saved, current_cabinet
        
        scrolls = 0
        while scrolls < ATTEMPTS * 20:
            _, first_name_element, is_first_name_found = find_task_by_name(driver, names_to_save[0])
            if is_first_name_found == 'not_found' and first_name_element is None:
                click_tasks_history(driver)
                scrolls += 1
                continue
            break
        else:
            print("Первая задача из списка не найдена")
            return added_and_saved, current_cabinet
        
        if not click_safely(first_name_element):
            print("Не удалось нажать на задачу")
            return added_and_saved, current_cabinet
        
        while True:
            export_button = WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, ".//button[contains(@onclick, 'view.save_to_audience')]"))
            )
            if not click_safely(export_button):
                print("Не удалось нажать на кнопку экспорта")
                return added_and_saved, current_cabinet
            
            # all_cabinet_buttons_sorted = get_and_choose_cabinets(driver)
            all_cabinet_buttons_sorted = get_and_choose_cabinets(driver, cabinets_type, cabinets_mode, cabinets)
            if len(all_cabinet_buttons_sorted) == 0:
                return added_and_saved, current_cabinet
            
            if current_cabinet is None:
                index = 0
                cabinet_button = all_cabinet_buttons_sorted[index][0]
                current_cabinet = all_cabinet_buttons_sorted[index][1]
            else:
                index = -1
                for i, (btn, text) in enumerate(all_cabinet_buttons_sorted):
                    if text == current_cabinet:
                        cabinet_button = btn
                        index = i
                        break
                if index == -1:
                    print(f"Кабинет {current_cabinet} не найден в списке")
                    return added_and_saved, current_cabinet

            if not click_safely(cabinet_button):
                print("Не удалось нажать на кнопку выбора кабинета")
                return added_and_saved, current_cabinet
            print(f"Обработка кабинета: '{current_cabinet}'")

            names_to_save = get_names_to_save(db_path)

            for name in names_to_save[:CHUNK_SIZE]:
                print()

                if not add_audience_in_cabinet(driver, name):
                    update_value_in_db(db_path, name, 'cabinet', current_cabinet)
                    update_value_in_db(db_path, name, 'add_status', False)
                    continue

                if check_audience_limit(driver) or check_error(driver):
                    update_value_in_db(db_path, name, 'cabinet', current_cabinet)
                    update_value_in_db(db_path, name, 'add_status', False)
                    if index == len(all_cabinet_buttons_sorted) - 1:
                        print(f"Все кабинеты переполнены")
                        return added_and_saved, current_cabinet
                    print(f"Лимит аудиторий в кабинете '{current_cabinet}'. Переключаемся на следующий")
                    # all_cabinet_buttons_sorted = get_and_choose_cabinets(driver)
                    all_cabinet_buttons_sorted = get_and_choose_cabinets(driver, cabinets_type, cabinets_mode, cabinets)
                    next_cabinet = all_cabinet_buttons_sorted[index + 1][1]
                    current_cabinet, cabinet_is_changed = next_cabinet, True
                    break

                print(f"Аудитория '{name}' создана в кабинете (окончательно)")
                update_value_in_db(db_path, name, 'cabinet', current_cabinet)
                update_value_in_db(db_path, name, 'add_status', True)

                if not save_audience_in_cabinet(driver, name):
                    continue
                print(f"Аудитория '{name}' создана и сохранена в кабинете")
                update_value_in_db(db_path, name, 'save_status', True)
                added_and_saved += 1
                

            if cabinet_is_changed:
                cabinet_is_changed = False
                continue

            print(f"Чанк из {CHUNK_SIZE} записей обработан. Добавлено и сохранено {added_and_saved} аудиторий\n")
            return added_and_saved, current_cabinet
    
    except Exception as e:
        print(f"Ошибка в пайплайне добавления и сохранения задач: {str(e)}")

    return added_and_saved, current_cabinet

def pipeline_tasks_adding_and_saving(driver, db_path, cabinets_type, cabinets_mode, cabinets, need_reload=True):
    added_and_saved = 0
    current_cabinet = None

    while True:
        names_to_save = get_names_to_save(db_path)
        if len(names_to_save) == 0:
            print(f"Всего добавлено и сохранено аудиторий: {added_and_saved}")
            return added_and_saved

        result, current_cabinet = chunk_pipeline_tasks_adding_and_saving(
            driver, db_path, cabinets_type, cabinets_mode, cabinets, current_cabinet, need_reload
        )
        added_and_saved += result


def prepare_output_dir(output_dir):
    print('Подготовка выходной директории')

    if os.path.exists(output_dir) and os.path.isdir(output_dir):
        print(f'Директория {output_dir} уже существует')
    else:
        os.makedirs(output_dir, exist_ok=True)
        print(f'Создана директория {output_dir}')


def get_saved_names(db_path, saved_names_path):
    saved_names = pd.DataFrame(get_names_from_db_by_status(db_path, 'save_status', include_values=[True]), columns=['name'])
    saved_names.to_excel(saved_names_path, header=None, index=False)
    return saved_names

def get_big_names(db_path, big_names_path):
    big_names = pd.DataFrame(get_names_from_db_by_status_in_saved_range(db_path, ['too_many']), columns=['name'])
    big_names.to_excel(big_names_path, header=None, index=False)
    return big_names

def get_big_and_saved_names(db_path, big_and_saved_names_path):
    big_and_saved_names = pd.DataFrame(get_names_from_db_by_status_in_saved_range(db_path, ['too_many', 'in_range']), columns=['name'])
    big_and_saved_names.to_excel(big_and_saved_names_path, header=None, index=False)
    return big_and_saved_names

def get_cabinets(db_path):
    cabinets = pd.DataFrame(get_distinct_cabinets_from_db(db_path), columns=['cabinet'])
    cabinets.sort_values(by='cabinet', key=lambda x: x.apply(get_cabinet_number), inplace=True, ignore_index=True)
    return cabinets
