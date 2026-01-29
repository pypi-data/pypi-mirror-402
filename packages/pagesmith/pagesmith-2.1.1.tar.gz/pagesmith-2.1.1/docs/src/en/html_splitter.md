# HTML pages

## Split HTML to Pages

Use class [HtmlPageSplitter][pagesmith.HtmlPageSplitter]

```python
from pagesmith import HtmlPageSplitter

html = """
<p>Start of text
<a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">
This is a link with a very long text that should be split across pages but the tag itself should stay intact
</a>
<span class="another-long-class-that-should-not-be-split">
More text that goes on and on and should also be split into multiple pages while preserving the HTML structure
</span>
</p>
"""

for page in HtmlPageSplitter(html, target_length=50).pages():
    print(page)
```

!!! example "Resulting pages"

    === "Page 1"
        ```html
        <p>Start of text
        </p><p><a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">
        This is a link with a very long text that </a></p>
        ```

    === "Page 2"
        ```html
        <p><a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">should be split across pages but the tag itself </a></p>
        ```

    === "Page 3"
        ```html
        <p><a href="../Text/chapter1.xhtml" class="very-long-class-name-to-force-splitting">should stay intact
        </a></p><p><span class="another-long-class-that-should-not-be-split">
        More text that goes on and on and should </span></p>
        ```

    === "Page 4"
        ```html
        <p><span class="another-long-class-that-should-not-be-split">also be split into multiple pages while preserving </span></p>
        ```

    === "Page 5"
        ```html
        <p><span class="another-long-class-that-should-not-be-split">the HTML structure
        </span></p>
        ```

## Refine HTML

[refine_html][pagesmith.refine_html.refine_html] is a utility for cleaning up HTML content.

It removes unnecessary for reading tags and vertical gaps.
