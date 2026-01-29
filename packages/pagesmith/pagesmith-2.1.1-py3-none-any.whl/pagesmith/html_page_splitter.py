import copy
from collections.abc import Iterator
from typing import Any

from lxml import etree

from pagesmith.parser import etree_to_str, parse_partial_html

PAGE_LENGTH_TARGET = 3000  # Target page length in characters
PAGE_LENGTH_ERROR_TOLERANCE = 0.25  # Tolerance for page length error


def _get_nsmap(attrib: dict[str, str]) -> dict[str, str] | None:
    """Extract namespace map from attributes to keep parser happy."""
    nsmap = {}
    for attr_name in attrib:
        if ":" in attr_name:
            prefix = attr_name.split(":", 1)[0]
            if prefix not in nsmap:
                nsmap[prefix] = {"epub": "http://www.idpf.org/2007/ops"}.get(
                    prefix,
                    f"http://example.com/ns/{prefix}",
                )
    return nsmap if nsmap else None


def _set_attributes(
    element: etree._Element,
    attrib: dict[str, str],
    nsmap: dict[str, str] | None,
) -> None:
    """Set attributes on element, handling namespaced attributes with QName."""
    for attr_name, attr_value in attrib.items():
        if ":" in attr_name and nsmap:
            prefix = attr_name.split(":", 1)[0]
            if prefix in nsmap:
                qname = etree.QName(nsmap[prefix], attr_name.split(":", 1)[1])
                element.set(qname, attr_value)
            else:
                element.set(attr_name, attr_value)
        else:
            element.set(attr_name, attr_value)


class HtmlPageSplitter:
    """Split HTML into pages,
    preserving HTML tags while respecting the original document structure.
    """

    def __init__(
        self,
        content: str = "",
        *,
        root: etree._Element | None = None,
        target_length: int = PAGE_LENGTH_TARGET,
        error_tolerance: float = PAGE_LENGTH_ERROR_TOLERANCE,
    ) -> None:
        """Initialize the HTML page splitter.

        Args:
            content: HTML content string to split (optional if root is provided)
            root: Parsed lxml element tree root (optional if content is provided)
            target_length: Target size for each page in characters
            error_tolerance: Tolerance for page size variation (default 0.25)
        """
        self.target_page_size = target_length
        self.max_size = int(target_length * (1 + error_tolerance))
        self.max_error = self.max_size - target_length

        if root is not None:
            self.root = root
        elif content is not None and content.strip():
            self.root = parse_partial_html(content)
        else:
            self.root = None

    def pages(self) -> Iterator[str]:
        """Split content into pages."""
        if self.root is None:
            return
        current_page: list[etree.Element] = []
        current_size = 0

        for element in self._split_element(self.root):
            element_size = self._get_element_size(element)

            # Check if adding this element would exceed page size
            if current_size + element_size > self.max_size and current_page:
                yield self._render_page(current_page)
                current_page = []
                current_size = 0

            current_page.append(element)
            current_size += element_size

        # Yield final page if there's content
        if current_page:
            yield self._render_page(current_page)

    def _split_element(self, element: etree._Element) -> Iterator[etree._Element]:  # noqa: PLR0915,PLR0912,C901
        """Recursively split an element if it's too large."""
        element_size = self._get_element_size(element)

        # If element is small enough, yield it as is
        if element_size <= self.max_size:
            # Special handling for body elements - yield their children instead
            if getattr(element, "tag", None) == "body":
                for child in element:
                    yield copy.deepcopy(child)
                return
            yield copy.deepcopy(element)
            return

        # Element is too large - try to split it

        if getattr(element, "tag", None) == "body":
            # Treat body's children as if they were at the root level
            for child in element:
                yield from self._split_element(child)
            return

        # If element has no children, it must have large text content or tail
        if len(element) == 0:
            yield from self._split_text_element(element)
            return

        # Element has children - we need to handle:
        # 1. element.text (before first child)
        # 2. each child and its tail text
        # We'll build up a list of content items and then group them into pages

        content_items: list[tuple[str, Any]] = []

        # Handle text before first child
        if element.text and element.text.strip():
            if len(element.text) > self.max_size:
                # Split the text
                text_chunks = self._split_text(element.text)
                content_items.extend(("text", chunk) for chunk in text_chunks)
            else:
                content_items.append(("text", element.text))

        # Process each child and its tail
        for child in element:
            # Recursively split the child
            content_items.extend(
                ("element", split_child) for split_child in self._split_element(child)
            )
            # Handle tail text of the original child
            if child.tail and child.tail.strip():
                if len(child.tail) > self.target_page_size:
                    # Split the tail text
                    tail_chunks = self._split_text(child.tail)
                    content_items.extend(("tail", chunk) for chunk in tail_chunks)
                else:
                    content_items.append(("tail", child.tail))

        # Now group content items into pages
        nsmap = _get_nsmap(element.attrib)
        current_shell = etree.Element(element.tag, nsmap=nsmap)
        _set_attributes(current_shell, element.attrib, nsmap)
        current_size = 0

        for item_type, item_content in content_items:
            item_size = 0  # initialized here only to satisfy type checker
            if item_type == "text":
                # This is text that goes at the beginning of the element
                if not current_shell.text:
                    current_shell.text = item_content
                else:
                    current_shell.text += item_content
                item_size = len(item_content)
            elif item_type == "element":
                # This is a child element
                item_size = self._get_element_size(item_content)
                if current_size + item_size > self.target_page_size and (
                    len(current_shell) > 0 or current_shell.text
                ):
                    # Yield current shell and start a new one
                    yield current_shell
                    current_shell = etree.Element(element.tag, nsmap=nsmap)
                    _set_attributes(current_shell, element.attrib, nsmap)
                    current_size = 0
                current_shell.append(item_content)
            elif item_type == "tail":
                # This is tail text that should follow the last child
                item_size = len(item_content)
                if current_size + item_size > self.target_page_size and (
                    len(current_shell) > 0 or current_shell.text
                ):
                    # Yield current shell and start a new one
                    yield current_shell
                    current_shell = etree.Element(element.tag, nsmap=nsmap)
                    _set_attributes(current_shell, element.attrib, nsmap)
                    current_size = 0

                if len(current_shell) > 0:
                    # Add as tail to the last child
                    last_child = current_shell[-1]
                    if last_child.tail:
                        last_child.tail += item_content
                    else:
                        last_child.tail = item_content
                # No children yet, add as text
                elif current_shell.text:
                    current_shell.text += item_content
                else:
                    current_shell.text = item_content

            current_size += item_size

        # Yield final shell if it has content
        if len(current_shell) > 0 or current_shell.text:
            yield current_shell

    def _split_text_element(self, element: etree._Element) -> Iterator[etree._Element]:
        """Split an element that has only text content."""
        text = element.text or ""
        if not text:
            yield copy.deepcopy(element)
            return

        chunks = self._split_text(text)
        nsmap = _get_nsmap(element.attrib)
        for chunk in chunks:
            new_elem = etree.Element(element.tag, nsmap=nsmap)
            _set_attributes(new_elem, element.attrib, nsmap)
            new_elem.text = chunk
            yield new_elem

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks that fit within page size."""
        if not text or len(text) <= self.target_page_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Find end position for this chunk
            end = start + self.target_page_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # Find a good break point
            break_pos = self._find_break_point(text, start, end)
            chunks.append(text[start:break_pos])
            start = break_pos

        return chunks

    def _find_break_point(self, text: str, start: int, target_end: int) -> int:
        """Find the best position to break text."""
        if target_end >= len(text):
            return len(text)

        # Look for break points in order of preference
        break_sequences = [
            "\n\n",  # Paragraph break
            ".\n",  # Sentence end with newline
            "!\n",  # Exclamation with newline
            "?\n",  # Question with newline
            ". ",  # Sentence end
            "! ",  # Exclamation
            "? ",  # Question
            "\n",  # Line break
            "; ",  # Semicolon
            ", ",  # Comma
            " ",  # Space
        ]

        search_start = max(start, target_end - self.max_error)
        search_end = min(len(text), target_end + self.max_error)

        for break_seq in break_sequences:
            # Search backward from target
            for pos in range(target_end, search_start, -1):
                if text[pos : pos + len(break_seq)] == break_seq:
                    return pos + len(break_seq)

            # Search forward from target (but not too far to avoid exceeding limits)
            for pos in range(target_end, search_end):
                if text[pos : pos + len(break_seq)] == break_seq:
                    return pos + len(break_seq)

        # No good break point found - break at target
        return target_end

    def _get_element_size(self, element: etree._Element) -> int:
        """Calculate the size of an element in characters."""
        return len(etree.tostring(element, method="text", encoding="unicode").strip())

    def _render_page(self, elements: list[etree._Element]) -> str:
        """Render a page from a list of elements."""
        if len(elements) == 1:
            return etree_to_str(elements[0])
        return "".join(etree_to_str(elem) for elem in elements)
