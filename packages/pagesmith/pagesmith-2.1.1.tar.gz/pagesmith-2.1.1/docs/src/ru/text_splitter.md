# Текстовые страницы

## Разбиение текста на страницы

С помощью класса [PageSplitter][pagesmith.PageSplitter]

```python
from pagesmith import PageSplitter

text = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""
for page in PageSplitter(text, target_page_size=50).pages():
    print(page)
```

## Обнаружение глав в тексте

Используйте класс [ChapterDetector][pagesmith.ChapterDetector] для поиска заголовков глав в обычном тексте.

```python
from pagesmith import ChapterDetector

page1_text = """
Здесь какой-то вводный текст.

Глава 1. Начало

Это содержимое первой главы с большим количеством текста, который продолжается и продолжается.

Глава 2. Развитие

Больше содержимого здесь для второй главы.

XII. Последняя глава

Заключительное содержимое.
"""

detector = ChapterDetector()
chapters = detector.get_chapters(page1_text)

for chapter in chapters:
    print(f"{chapter.title} (позиция {chapter.position})")
```

!!! example "Результат"

    ```
    Глава 1. Начало (позиция 42)
    Глава 2. Развитие (позиция 134)
    XII. Последняя глава (позиция 201)
    ```

Детектор распознает различные форматы глав:

- "Chapter 1", "Chapter I", "Chapter one"
- "1. Заголовок", "XII. Заголовок"
- Многоязычные: "Глава 1", "Glava 1"
