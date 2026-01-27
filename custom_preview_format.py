"""
Решение для генерации превью изображений в кастомном формате
Поддержка любых соотношений сторон, заданных пользователем
"""

from PIL import Image
from typing import Tuple


class CustomPreviewGenerator:
    """Генератор превью с поддержкой кастомных форматов"""
    
    def __init__(self):
        # Предустановленные форматы (для справки)
        self.preset_formats = {
            "32:9": (32, 9),
            "24:9": (24, 9),
            "21:9": (21, 9),
            "16:10": (16, 10),
            "16:9": (16, 9),
            "4:3": (4, 3),
            "5:4": (5, 4),
            "3:2": (3, 2),
        }
    
    def parse_aspect_ratio(self, format_str: str) -> Tuple[int, int]:
        """
        Парсит строку формата в соотношение сторон
        
        Args:
            format_str: Строка вида "24:9" или "16:9"
            
        Returns:
            Кортеж (ширина, высота)
        """
        try:
            width, height = map(int, format_str.split(':'))
            return (width, height)
        except:
            raise ValueError(f"Неверный формат: {format_str}. Ожидается 'ширина:высота'")
    
    def calculate_dimensions(
        self, 
        aspect_ratio: Tuple[int, int], 
        target_width: int = None,
        target_height: int = None
    ) -> Tuple[int, int]:
        """
        Вычисляет размеры изображения на основе соотношения сторон
        
        Args:
            aspect_ratio: Кортеж (ширина, высота) соотношения
            target_width: Целевая ширина (если задана)
            target_height: Целевая высота (если задана)
            
        Returns:
            Кортеж (ширина_px, высота_px)
        """
        ratio_w, ratio_h = aspect_ratio
        
        if target_width:
            # Вычисляем высоту на основе ширины
            height = int(target_width * ratio_h / ratio_w)
            return (target_width, height)
        
        elif target_height:
            # Вычисляем ширину на основе высоты
            width = int(target_height * ratio_w / ratio_h)
            return (width, target_height)
        
        else:
            # Используем стандартный размер (например, 1920px по ширине)
            default_width = 1920
            height = int(default_width * ratio_h / ratio_w)
            return (default_width, height)
    
    def create_preview(
        self,
        input_image_path: str,
        output_path: str,
        format_str: str,
        target_width: int = 1920,
        crop_mode: str = "center"
    ):
        """
        Создает превью изображения в заданном формате
        
        Args:
            input_image_path: Путь к исходному изображению
            output_path: Путь для сохранения превью
            format_str: Формат в виде "24:9", "16:9" и т.д.
            target_width: Целевая ширина превью
            crop_mode: Режим обрезки ("center", "top", "bottom")
        """
        # Открываем исходное изображение
        img = Image.open(input_image_path)
        original_width, original_height = img.size
        
        # Парсим формат
        aspect_ratio = self.parse_aspect_ratio(format_str)
        
        # Вычисляем целевые размеры
        target_width, target_height = self.calculate_dimensions(
            aspect_ratio, 
            target_width=target_width
        )
        
        # Вычисляем соотношение сторон
        target_ratio = target_width / target_height
        original_ratio = original_width / original_height
        
        # Определяем, как обрезать изображение
        if original_ratio > target_ratio:
            # Исходное изображение шире целевого - обрезаем по ширине
            new_height = original_height
            new_width = int(original_height * target_ratio)
            
            # Определяем позицию обрезки по горизонтали
            if crop_mode == "center":
                left = (original_width - new_width) // 2
            elif crop_mode == "left":
                left = 0
            else:  # right
                left = original_width - new_width
            
            top = 0
            right = left + new_width
            bottom = original_height
            
        else:
            # Исходное изображение выше целевого - обрезаем по высоте
            new_width = original_width
            new_height = int(original_width / target_ratio)
            
            # Определяем позицию обрезки по вертикали
            if crop_mode == "center":
                top = (original_height - new_height) // 2
            elif crop_mode == "top":
                top = 0
            else:  # bottom
                top = original_height - new_height
            
            left = 0
            right = original_width
            bottom = top + new_height
        
        # Обрезаем изображение
        img_cropped = img.crop((left, top, right, bottom))
        
        # Изменяем размер до целевого
        img_resized = img_cropped.resize(
            (target_width, target_height),
            Image.Resampling.LANCZOS
        )
        
        # Сохраняем
        img_resized.save(output_path, quality=95, optimize=True)
        
        print(f"✅ Превью создано:")
        print(f"   Формат: {format_str}")
        print(f"   Размер: {target_width}x{target_height}px")
        print(f"   Сохранено: {output_path}")


# ПРИМЕР ИСПОЛЬЗОВАНИЯ
if __name__ == "__main__":
    generator = CustomPreviewGenerator()
    
    # Пример 1: Создание превью в формате 24:9
    print("=" * 60)
    print("Пример 1: Формат 24:9 (ваш кастомный формат)")
    print("=" * 60)
    
    # generator.create_preview(
    #     input_image_path="input.jpg",
    #     output_path="preview_24_9.jpg",
    #     format_str="24:9",
    #     target_width=1920,
    #     crop_mode="center"
    # )
    
    # Пример 2: Расчет размеров для разных форматов
    print("\n" + "=" * 60)
    print("Пример 2: Расчет размеров для разных форматов")
    print("=" * 60)
    
    formats = ["24:9", "16:9", "21:9", "32:9", "4:3"]
    target_width = 1920
    
    print(f"\nПри целевой ширине {target_width}px:\n")
    for fmt in formats:
        ratio = generator.parse_aspect_ratio(fmt)
        width, height = generator.calculate_dimensions(ratio, target_width=target_width)
        print(f"  {fmt:6} → {width}x{height}px")
    
    # Пример 3: Произвольный формат
    print("\n" + "=" * 60)
    print("Пример 3: Произвольные кастомные форматы")
    print("=" * 60)
    
    custom_formats = ["24:9", "18:5", "7:3", "25:10"]
    
    print(f"\nПроизвольные форматы при ширине {target_width}px:\n")
    for fmt in custom_formats:
        try:
            ratio = generator.parse_aspect_ratio(fmt)
            width, height = generator.calculate_dimensions(ratio, target_width=target_width)
            print(f"  {fmt:6} → {width}x{height}px")
        except ValueError as e:
            print(f"  {fmt:6} → Ошибка: {e}")


"""
ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ В ВАШ КОД:

1. В вашем боте, где вы обрабатываете выбор формата, замените:

   БЫЛО:
   -------
   if user_format in preset_formats:
       use_format = preset_formats[user_format]
   else:
       use_format = preset_formats["16:9"]  # fallback
   
   СТАЛО:
   -------
   generator = CustomPreviewGenerator()
   
   # Используем формат пользователя напрямую
   generator.create_preview(
       input_image_path=original_image_path,
       output_path=preview_path,
       format_str=user_selected_format,  # "24:9" или любой другой
       target_width=1920,
       crop_mode="center"
   )

2. Если у вас формат хранится как строка "24:9":
   
   user_format = "24:9"  # Из выбора пользователя
   
   generator.create_preview(
       input_image_path="source.jpg",
       output_path="preview.jpg",
       format_str=user_format,
       target_width=1920
   )

3. Если нужно поддерживать и старые preset форматы:
   
   # Сначала проверяем, есть ли в базе кастомный формат
   if user_custom_format:
       format_to_use = user_custom_format  # "24:9"
   else:
       format_to_use = "16:9"  # default
   
   generator.create_preview(
       input_image_path=img_path,
       output_path=preview_path,
       format_str=format_to_use
   )

ОСНОВНЫЕ ПРЕИМУЩЕСТВА:
✅ Поддержка ЛЮБОГО формата (24:9, 18:5, 7:3, что угодно)
✅ Автоматический расчет размеров
✅ Интеллектуальная обрезка (center/top/bottom)
✅ Сохранение качества изображения
✅ Простая интеграция в существующий код
"""
