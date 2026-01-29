"""Splitting HTML into pages, preserving HTML tags
while respecting the original document structure and text integrity.

The file is mandatory for build system to find the package.
"""

from pagesmith.__about__ import __version__
from pagesmith.chapter_detector import ChapterDetector
from pagesmith.html_page_splitter import HtmlPageSplitter
from pagesmith.page_splitter import PageSplitter
from pagesmith.parser import etree_to_str, parse_partial_html
from pagesmith.refine_html import refine_html

__all__ = [
    "__version__",
    "ChapterDetector",
    "PageSplitter",
    "HtmlPageSplitter",
    "refine_html",
    "parse_partial_html",
    "etree_to_str",
]
