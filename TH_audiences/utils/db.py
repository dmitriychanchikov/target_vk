from typing import Union, List, Optional, Iterable

import pandas as pd
import sqlite3


ALLOWED_COLUMNS = [
    "create_status", "search_status", "accounts_count", "count_status",
    "cabinet", "add_status", "save_status", "notes"
]


def load_data(data_path):
    try:
        df = pd.read_excel(data_path, header=None)
        print(f"Данные из файла '{data_path}' успешно загружены в DataFrame")
        return df
        
    except FileNotFoundError:
        print(f"Файл '{data_path}' не найден")
        return None

    except Exception as e:
        print(f"Ошибка при загрузке файла '{data_path}': {str(e)}")
        return None


def init_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='results'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                create_status BOOLEAN DEFAULT NULL,
                search_status TEXT DEFAULT NULL
                    CHECK(search_status IN ('not_found', 'running', 'stopped', 'found')),
                accounts_count INTEGER DEFAULT NULL,
                count_status TEXT DEFAULT NULL
                    CHECK(count_status IN ('too_few', 'in_range', 'too_many')),
                cabinet TEXT DEFAULT NULL,
                add_status BOOLEAN DEFAULT NULL,
                save_status BOOLEAN DEFAULT NULL,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
            ''')
            conn.commit()
            print(f"Таблица 'results' успешно создана в БД '{db_path}'")
        else:
            print(f"Таблица 'results' уже существует в БД '{db_path}'")
        return True

    except FileNotFoundError:
        print(f"Файл '{db_path}' не найден")
        return False

    except sqlite3.Error as e:
        print(f"Ошибка при инициализации БД: {e}")
        return False

    finally:
        if conn:
            conn.close()


def insert_names_from_df_to_db(db_path, df):
    try:
        records = [(name,) for name in df.iloc[:, 0]]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executemany('''
        INSERT OR IGNORE INTO results (name, last_update)
        VALUES (?, CURRENT_TIMESTAMP)
        ''', records)
        conn.commit()
        print(f"Из DataFrame добавлено {len(records)} записей в БД")
        return True
        
    except sqlite3.Error as e:
        print(f"Ошибка при вставке данных в БД: {e}")
        return False
    
    finally:
        if conn:
            conn.close()


def update_value_in_db(db_path, name, column, value):
    if column not in ALLOWED_COLUMNS:
        print(f"Недопустимая колонка: '{column}'. Разрешены: {ALLOWED_COLUMNS}")
        return False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if value is None:
            sql = f"""
                UPDATE results
                SET {column} = NULL,
                    last_update = CURRENT_TIMESTAMP
                WHERE name = ?
            """
            cursor.execute(sql, (name,))
        else:
            sql = f"""
                UPDATE results
                SET {column} = ?,
                    last_update = CURRENT_TIMESTAMP
                WHERE name = ?
            """
            cursor.execute(sql, (value, name))

        conn.commit()
        print(f"Значение '{column}' для записи '{name}' успешно обновлено в БД")
        return cursor.rowcount > 0
    
    except sqlite3.Error as e:
        print(f"Ошибка при обновлении данных в БД: {e}")
        return False
    
    finally:
        if conn:
            conn.close()
        

def update_column_value_in_db(db_path: str, column: str, value: Optional[object] = None) -> bool:
    """
    Устанавливает одинаковое значение для всех строк в указанной колонке.
    По умолчанию value=None (NULL).
    """
    if column not in ALLOWED_COLUMNS:
        print(f"Недопустимая колонка: '{column}'. Разрешены: {ALLOWED_COLUMNS}")
        return False

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if value is None:
            sql = f"""
                UPDATE results
                SET {column} = NULL,
                    last_update = CURRENT_TIMESTAMP
            """
            cursor.execute(sql)
        else:
            sql = f"""
                UPDATE results
                SET {column} = ?,
                    last_update = CURRENT_TIMESTAMP
            """
            cursor.execute(sql, (value,))

        conn.commit()
        print(f"Значение '{column}' для {cursor.rowcount} записей успешно обновлено в БД")
        return cursor.rowcount > 0
    
    except sqlite3.Error as e:
        print(f"Ошибка при массовом обновлении данных в БД: {e}")
        return False
    
    finally:
        if conn:
            conn.close()


def delete_by_name_in_db(db_path: str, name: str) -> bool:
    """
    Удаляет строку из таблицы results по точному совпадению name.
    Возвращает True, если удалена хотя бы одна строка.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM results WHERE name = ?", (name,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Запись '{name}' успешно удалена из БД")
            return True
        else:
            print(f"Запись '{name}' не найдена в БД")
            return False
    except sqlite3.Error as e:
        print(f"Ошибка при удалении записи из БД: {e}")
        return False
    finally:
        if conn:
            conn.close()


def migrate_common_records_between_db(new_db_path: str, old_db_path: str, table: str = "results"):
    """
    Переносит записи из старой БД в новую, если поле `name` совпадает.
    
    :param new_db_path: путь к новой базе (куда переносим)
    :param old_db_path: путь к старой базе (откуда берем данные)
    :param table: имя таблицы (одинаковое в обеих БД)
    """
    # Подключаемся к обеим БД
    new_conn = sqlite3.connect(new_db_path)
    old_conn = sqlite3.connect(old_db_path)
    new_cur = new_conn.cursor()
    old_cur = old_conn.cursor()

    try:
        # Получим имена колонок для универсальности
        new_cur.execute(f"PRAGMA table_info({table})")
        columns_info = new_cur.fetchall()
        columns = [col[1] for col in columns_info]  # имена всех колонок
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))

        # 1) Собираем все имена из новой базы
        new_cur.execute(f"SELECT name FROM {table}")
        new_names = set(row[0] for row in new_cur.fetchall())

        # 2) Достаём данные из старой базы по совпадающим именам
        if new_names:
            placeholders_names = ", ".join("?" for _ in new_names)
            old_cur.execute(
                f"SELECT {columns_str} FROM {table} WHERE name IN ({placeholders_names})",
                tuple(new_names)
            )
            rows_to_insert = old_cur.fetchall()

            # 3) Обновляем записи в новой БД данными из старой
            if rows_to_insert:
                col_names = [col for col in columns if col != "id" and col != "name"]
                set_expr = ", ".join([f"{col} = ?" for col in col_names])

                for row in rows_to_insert:
                    row_dict = dict(zip(columns, row))
                    update_values = [row_dict[col] for col in col_names] + [row_dict["name"]]
                    new_cur.execute(
                        f"UPDATE {table} SET {set_expr} WHERE name = ?",
                        update_values
                    )

                print(f"Обновлено {len(rows_to_insert)} записей.")

        new_conn.commit()

    finally:
        old_conn.close()
        new_conn.close()


def get_names_from_db_by_status(
    db_path: str,
    status_column: str,
    *,
    include_values: Optional[list] = None,
    exclude_values: Optional[list] = None,
    with_id: bool = False,
) -> list:
    """
    Получает имена из БД по заданным критериям статуса
    
    :param db_path: Путь к файлу БД
    :param status_column: Название колонки со статусом
    :param include_values: Список включаемых значений (None - все значения)
    :param exclude_values: Список исключаемых значений
    :param exact_match: True - точное совпадение, False - частичное (LIKE)
    :return: Список имен, удовлетворяющих условиям
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if with_id:
            query = "SELECT id, name FROM results WHERE "
        else:
            query = "SELECT name FROM results WHERE "
        params = []
        
        # Обработка NULL значений
        if include_values:
            if None in include_values:
                include_values = [v for v in include_values if v is not None]
                if include_values:
                    query += f"({status_column} IS NULL OR {status_column} IN ({','.join(['?']*len(include_values))}))"
                    params.extend(include_values)
                else:
                    query += f"{status_column} IS NULL"
            else:
                query += f"{status_column} IN ({','.join(['?']*len(include_values))})"
                params.extend(include_values)
        else:
            query += f"{status_column} IS NOT NULL"
        
        # Добавляем исключения
        if exclude_values:
            if None in exclude_values:
                exclude_values = [v for v in exclude_values if v is not None]
                if exclude_values:
                    query += f" AND {status_column} IS NOT NULL AND {status_column} NOT IN ({','.join(['?']*len(exclude_values))})"
                    params.extend(exclude_values)
                else:
                    query += f" AND {status_column} IS NOT NULL"
            else:
                query += f" AND {status_column} NOT IN ({','.join(['?']*len(exclude_values))})"
                params.extend(exclude_values)
        
        # print(query)
        # print(params)
        cursor.execute(query, params)
        if with_id:
            return [row for row in cursor.fetchall()]
        else:
            return [row[0] for row in cursor.fetchall()]
        
    except sqlite3.Error as e:
        print(f"Ошибка при чтении из БД: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_names_from_db_by_status_in_saved_range(
    db_path: str,
    statuses: Iterable[str]  # например: ['too_many'] или ['too_many','in_range']
) -> List[str]:
    """
    Возвращает name из диапазона [min(id), max(id)] по строкам, где save_status=1,
    отфильтрованные по списку статусов в count_status.
    """
    statuses = list(statuses)
    if not statuses:
        print("Пустой список статусов — вернётся пустой результат")
        return []

    placeholders = ",".join(["?"] * len(statuses))
    sql = f"""
    WITH bounds AS (
      SELECT MIN(id) AS lo, MAX(id) AS hi
      FROM results
      WHERE save_status = 1
    )
    SELECT name
    FROM results, bounds
    WHERE id BETWEEN lo AND hi
      AND count_status IN ({placeholders});
    """
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, statuses)
        return [row[0] for row in cur.fetchall()]
    except sqlite3.Error as e:
        print(f"Ошибка при чтении из БД: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_distinct_cabinets_from_db(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            WITH bounds AS (
              SELECT MIN(id) AS lo, MAX(id) AS hi
              FROM results
              WHERE save_status = 1
            )
            SELECT DISTINCT cabinet
            FROM results, bounds
            WHERE cabinet IS NOT NULL
              AND id BETWEEN lo AND hi
        """)
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Ошибка при чтении из БД: {e}")
        return []
    finally:
        if conn:
            conn.close()


# def get_tasks_by_status_from_db(
#     db_path: str,
#     status_column: str,
#     status: Union[str, List[str]],
#     limit: Optional[int] = None
# ) -> List[str]:
#     """
#     Получает список задач по указанному статусу
    
#     :param db_path: Путь к файлу БД
#     :param column: Название колонки со статусом
#     :param status: Одно или несколько значений статуса
#     :param limit: Ограничение количества результатов
#     :return: Список имен задач
#     """
#     try:
#         conn = sqlite3.connect(db_path)
#         cursor = conn.cursor()
        
#         # Подготовка параметров
#         if isinstance(status, str):
#             status = [status]
        
#         placeholders = ','.join(['?'] * len(status))
#         query = f'''
#         SELECT name FROM results 
#         WHERE {status_column} IN ({placeholders})
#         {'LIMIT ?' if limit is not None else ''}
#         '''
        
#         params = status
#         if limit is not None:
#             params.append(limit)
        
#         cursor.execute(query, params)
#         results = [row[0] for row in cursor.fetchall()]
        
#         print(f"Найдено {len(results)} задач со статусом {status} в колонке '{status_column}'")
#         return results
        
#     except sqlite3.Error as e:
#         print(f"Ошибка при выборке данных из БД: {e}")
#         return []
    
#     finally:
#         if conn:
#             conn.close()




