import math
import os
import shutil

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


def scale_image(input_image, scale_factor=1):
    """
    Масштабирует изображение с заданным коэффициентом и выводит результат.
    
    Параметры:
    - input_image: исходное изображение (может быть путем к файлу или объектом numpy.ndarray)
    - scale_factor: коэффициент масштабирования (например, 0.5 для уменьшения в 2 раза, 2.0 для увеличения в 2 раза)
    """
    # Если input_image - это путь к файлу, загружаем изображение
    if isinstance(input_image, str):
        image = cv2.imread(input_image)
        if image is None:
            raise ValueError("Не удалось загрузить изображение по указанному пути")
    else:
        image = input_image.copy()
    
    # Получаем новые размеры
    height, width = image.shape[:2]
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    # Масштабируем изображение
    scaled_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    
    # Выводим результат
    cv2.imshow("Scaled Image", scaled_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def create_text_image(text, font_path, font_size, color, padding):
    """
    Создает изображение с текстом и прозрачным фоном используя PIL
    
    Параметры:
        text: текст для отображения
        font_path: путь к файлу шрифта (.ttf)
        font_size: размер шрифта
        color: цвет текста в формате (R, G, B, A)
        padding: отступ вокруг текста в пикселях (top, bottom, left, right)
    
    Возвращает:
        Изображение OpenCV (BGR) с прозрачным фоном
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        print(f"Шрифт {font_path} не найден, используется стандартный")
        font = ImageFont.load_default()
    
    # Получаем размер текста
    text_bbox = font.getbbox(text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Создаем изображение с альфа-каналом
    img = Image.new('RGBA', (text_width + padding[2] + padding[3], text_height + padding[0] + padding[1]), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Рисуем текст
    draw.text((padding[2], padding[0]), text, font=font, fill=color)
    
    # Конвертируем в OpenCV формат
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)

def rotate_text_image(text_img, angle):
    h, w = text_img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1)

    new_text_img = cv2.warpAffine(text_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)

    return new_text_img

def overlay_rotated_text(target_img, text_img, pos):
    """
    Накладывает повернутое изображение с текстом на целевое изображение
    
    Параметры:
        target_img: целевое изображение OpenCV (BGR)
        text_img: изображение с текстом (BGRA)
        pos: (x,y) позиция центра текста
        angle: угол поворота в градусах
    
    Возвращает:
        Изображение OpenCV (BGR) с наложенным текстом
    """
    # Конвертируем целевое изображение в BGRA
    target_bgra = cv2.cvtColor(target_img, cv2.COLOR_BGR2BGRA)
    
    # Получаем размеры текстового изображения
    h, w = text_img.shape[:2]
    
    # Вычисляем координаты для вставки
    x, y = pos
    x_start = max(0, x - w//2)
    y_start = max(0, y - h//2)
    x_end = min(target_bgra.shape[1], x_start + w)
    y_end = min(target_bgra.shape[0], y_start + h)
    
    # Область для вставки на целевом изображении
    target_roi = target_bgra[y_start:y_end, x_start:x_end]
    # target_roi = target_bgra
    
    # Область повернутого текста
    text_roi = text_img[max(0, h//2 - y):h - max(0, (y + h//2) - target_bgra.shape[0]),
                           max(0, w//2 - x):w - max(0, (x + w//2) - target_bgra.shape[1])]
    # scale_image(text_roi, 0.4)
    
    # Наложение с учетом альфа-канала
    alpha = text_roi[:, :, 3] / 255.0
    for c in range(3):
        target_roi[:, :, c] = target_roi[:, :, c] * (1 - alpha) + text_roi[:, :, c] * alpha
    
    # Конвертируем обратно в BGR
    return cv2.cvtColor(target_bgra, cv2.COLOR_BGRA2BGR)


def pipeline(names, template_path, font_path, photo_dir):
    if os.path.exists(photo_dir):
        shutil.rmtree(photo_dir)
    os.makedirs(photo_dir)

    template_image = cv2.imread(template_path)
    image = template_image.copy()

    line_coords = (552, 478, 712, 1078)
    line_dx = line_coords[2] - line_coords[0]
    line_dy = line_coords[3] - line_coords[1]
    line_angle_rad = math.atan2(line_dy, line_dx)
    line_angle_deg = math.degrees(line_angle_rad)

    for i, row in names.iterrows():
        name = row[0].replace('(', '').replace(')', '').split(' ')[0]
        print(f"Processing {i:3d} '{name}'")

        max_text_size = 105
        min_text_size = 40
        length_thresh = 2
        length_dec = 5
        text_size = max(
            min_text_size, 
            max_text_size - max(0, (len(name) - length_thresh)) * length_dec
        )
        text_image = create_text_image(
            text=name,
            font_path=font_path,
            font_size=text_size,
            color=(255, 255, 255, 240),
            padding=(75, 100, 100, 100)
        )

        text_angle_deg = 90 - line_angle_deg
        rotated_text_image = rotate_text_image(
            text_img=text_image,
            angle=text_angle_deg
        )

        text_line_ratio = 0.3
        text_pos_x = int(line_coords[0] + line_dx * text_line_ratio)
        text_pos_y = int(line_coords[1] + line_dy * text_line_ratio)
        new_image = overlay_rotated_text(
            target_img=image,
            text_img=rotated_text_image,
            pos=(text_pos_x, text_pos_y)
        )

        cv2.imwrite(f'{photo_dir}/temp.png', new_image)
        os.rename(f'{photo_dir}/temp.png', f'{photo_dir}/{name}.png')
