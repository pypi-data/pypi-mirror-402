import re

from lxml import etree, html

FAKE_ROOT = "pagesmith-root"
HTML_TAG_REPLACEMENT = "pagesmith-html"
SPECIAL_LXML_TAGS = {
    "html": HTML_TAG_REPLACEMENT,
    "head": "pagesmith-head",
    "body": "pagesmith-body",
}


def parse_partial_html(input_html: str) -> etree._Element | None:  # noqa: C901,PLR0912
    """Parse string with HTML fragment or full document into an lxml tree.

    Handles malformed HTML gracefully and preserves content structure as much as possible.

    Note:
        The returned element tree have a root wrapper element that simplifies operations with
        the result as single etree even if this is HTML fragments in some text without
        a single root.
        Use `etree_to_str()` to get the clean HTML output without the wrapper.

    Features:
    - Removes comments and CDATA sections
    - Handles partial/fragment HTML (no need for complete document structure)
    - Recovers from malformed HTML using lxml's error recovery
    - Suppress lxml special handling for tags `html`, `head`, `body` and treat them as normal tags

    Returns:
        lxml Element tree, wrapped in a 'root' container element
        or None if parsing completely fails
    """

    input_html = _normalize(input_html)

    # Clean up CDATA
    input_html = re.sub(r"(<!\[CDATA\[.*?]]>|<!DOCTYPE[^>]*?>)", "", input_html, flags=re.DOTALL)

    input_html = _rename_special_tags(input_html)

    parser = etree.HTMLParser(recover=True, remove_comments=True, remove_pis=True)
    try:
        result = html.fragment_fromstring(
            input_html,
            parser=parser,
            create_parent=FAKE_ROOT,
        )
    except Exception:  # noqa: BLE001
        result = html.Element(FAKE_ROOT)
        result.text = input_html

    return _restore_special_tags(result)


def etree_to_str(root: etree._Element | None) -> str:
    """Convert etree back to string, removing root wrapper."""
    if root is None:
        return ""

    if isinstance(root, str):
        return root

    # If this is our root wrapper, extract its contents
    if root.tag == FAKE_ROOT:
        result = root.text or ""
        for child in root:
            result += html.tostring(child, encoding="unicode", method="html")
        return result

    # For normal elements, return as-is using HTML serialization
    return html.tostring(root, encoding="unicode", method="html")  # type: ignore[no-any-return]


def unwrap_element(element: etree.Element) -> None:  # noqa: PLR0912,C901
    """Unwrap an element, replacing with its content."""
    parent = element.getparent()
    if parent is None:
        return

    pos = parent.index(element)

    # Handle text content
    if element.text:
        if pos > 0:
            # Add to tail of previous sibling
            prev = parent[pos - 1]
            if prev.tail:
                prev.tail += element.text
            else:
                prev.tail = element.text
        # Add to parent's text
        elif parent.text:
            parent.text += element.text
        else:
            parent.text = element.text

    # Move each child to parent
    children = list(element)
    for i, child in enumerate(children):
        parent.insert(pos + i, child)

    # Handle tail text
    if element.tail:
        if len(children) > 0:
            # Add to tail of last child
            if children[-1].tail:
                children[-1].tail += element.tail
            else:
                children[-1].tail = element.tail
        elif pos > 0:
            # Add to tail of previous sibling
            prev = parent[pos - 1]
            if prev.tail:
                prev.tail += element.tail
            else:
                prev.tail = element.tail
        # Add to parent's text
        elif parent.text:
            parent.text += element.tail
        else:
            parent.text = element.tail

    parent.remove(element)


def _rename_special_tags(input_html: str) -> str:
    """Replace HTML tags to avoid special treatment by lxml"""
    tags_pattern = "|".join(re.escape(tag) for tag in SPECIAL_LXML_TAGS)

    def replace_tag(match: re.Match[str]) -> str:
        slash, tag, attrs = match.groups()
        replacement = SPECIAL_LXML_TAGS[tag.lower()]
        return f"<{slash}{replacement}{attrs or ''}>"

    return re.sub(
        rf"<(/??)({tags_pattern})(\s[^>]*)?>",
        replace_tag,
        input_html,
        flags=re.IGNORECASE,
    )


def _restore_special_tags(result: etree._Element | None) -> etree._Element | None:
    """Rename special tags back to their original names in the parsed tree.

    If special tag duplicates are found, unwrap them instead to fix malformed HTML.
    """
    if isinstance(result, etree._Element):  # noqa: SLF001
        for tag, replacement in SPECIAL_LXML_TAGS.items():
            renamed_tags = result.xpath(f".//{replacement}")
            if len(renamed_tags) == 1:
                renamed_tags[0].tag = tag
            else:
                for element in renamed_tags:
                    unwrap_element(element)
    return result


def _normalize(input_html: str) -> str:
    """Normalize whitespaces and prevents information lost
    in lxml `remove_comments` functionality.
    """
    # Normalize whitespaces
    result = re.sub(r"[\n\r]+", " ", input_html)

    # Convert to text malformed HTML comments
    open_count = result.count("<!--")
    close_count = result.count("-->")
    if open_count != close_count:
        result = result.replace("<!--", "&lt;!--")
    return result.strip()
