# Text Pages

## Split Text to Pages

Use class [PageSplitter][pagesmith.PageSplitter]

```python
from pagesmith import PageSplitter

text = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""
for page in PageSplitter(text, target_page_size=50).pages():
    print(page)
```

## Detect Chapters in Text

Use class [ChapterDetector][pagesmith.ChapterDetector] to find chapter headings in plain text.

```python
from pagesmith import ChapterDetector

page1_text = """
Some introduction text here.

Chapter 1. The Beginning

This is the content of the first chapter with lots of text that goes on and on.

Chapter 2. The Development

More content here for the second chapter.

XII. The Final Chapter

The ending content.
"""

detector = ChapterDetector()
chapters = detector.get_chapters(page1_text)

for chapter in chapters:
    print(f"{chapter.title} (position {chapter.position})")
```

!!! example "Output"

    ```
    Chapter 1. The Beginning (position 42)
    Chapter 2. The Development (position 134)
    XII. The Final Chapter (position 201)
    ```

The detector recognizes various chapter formats:

- "Chapter 1", "Chapter I", "Chapter one"
- "1. Title", "XII. Title"
- Multilingual: "Глава 1", "Glava 1"
