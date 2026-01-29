# pagesmith

Splitting HTML into pages, preserving HTML tags while respecting the original document structure and text integrity.

Utilize blazingly fast lxml parser.

!!! note "How It Works"
    The [HtmlPageSplitter][pagesmith.HtmlPageSplitter] class intelligently splits HTML content into appropriately sized pages while ensuring all HTML tags remain properly closed and valid. This preserves both the document structure and styling.

You can use [refine_html][pagesmith.refine_html.refine_html] for refining HTML.

Also contains class for splitting to pages and extracting Table of Content from pure text

!!! note "How It Works"
    The [ChapterDetector][pagesmith.ChapterDetector] class analyzes text to find standard chapter heading formats. It automatically identifies the position of each chapter and extracts the title.

## Installation

```bash
pip install pagesmith
```

## Usage
- [HTML Pages](html_splitter.md)
- [Text Pages](text_splitter.md)
