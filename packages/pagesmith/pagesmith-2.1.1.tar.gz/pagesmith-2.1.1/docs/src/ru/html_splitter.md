# HTML страницы

## Разбиение HTML на страницы

С помощью класса [HtmlPageSplitter][pagesmith.HtmlPageSplitter]

```python
from pagesmith import HtmlPageSplitter

html = """
<p>Начало текста
<a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">
Это ссылка с очень длинным текстом, который должен быть разделен на страницы, но сам тег должен оставаться целым
</a>
<span class="another-long-class-that-should-not-be-split">
Дополнительный текст, который продолжается дальше и должен также быть разделен на несколько страниц при сохранении структуры HTML
</span>
</p>
"""

for page in HtmlPageSplitter(html, target_length=50).pages():
    print(page)
```

!!! example "Результирующие страницы"

    === "Страница 1"
        ```html
        <p>Начало текста
        </p><p><a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">
        Это ссылка с очень длинным текстом, который </a></p>
        ```

    === "Страница 2"
        ```html
        <p><a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">должен быть разделен на страницы, но сам тег </a></p>
        ```

    === "Страница 3"
        ```html
        <p><a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">должен оставаться целым
        </a></p><p><span class="another-long-class-that-should-not-be-split">
        Дополнительный текст, который продолжается </span></p>
        ```

    === "Страница 4"
        ```html
        <p><span class="another-long-class-that-should-not-be-split">дальше и должен также быть разделен на несколько </span></p>
        ```

    === "Страница 5"
        ```html
        <p><span class="another-long-class-that-should-not-be-split">страниц при сохранении структуры HTML
        </span></p>
        ```

## Очистка HTML

[refine_html][pagesmith.refine_html.refine_html] очищает HTML от не нужных для чтения тэгов и убирает излишние вертикальные промежутки.
