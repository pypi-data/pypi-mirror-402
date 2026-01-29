"""Split text into pages"""

import re
from collections.abc import Iterator

from pagesmith.chapter_detector import ChapterDetector

PAGE_LENGTH_TARGET = 3000  # Target page length in characters
PAGE_LENGTH_ERROR_TOLERANCE = 0.25  # Tolerance for page length error


class PageSplitter:
    """Split pure text into pages at natural break points such as paragraphs or sentences."""

    def __init__(
        self,
        text: str,
        *,
        start: int = 0,
        end: int = 0,
        target_length: int = PAGE_LENGTH_TARGET,
        error_tolerance: float = PAGE_LENGTH_ERROR_TOLERANCE,
    ):
        self.text = text
        self.start = start
        self.end = len(text) if end == 0 else end
        assert 0 < error_tolerance < 1
        self.target_length = target_length
        self.error_tolerance = error_tolerance
        self.min_length = int(
            self.target_length * (1 - self.error_tolerance),
        )
        self.max_length = int(
            self.target_length * (1 + self.error_tolerance),
        )

    def pages(self) -> Iterator[str]:
        """Split a text into pages of approximately equal length.

        Also clear headings and recollect them during pages generation.
        """
        chapter_detector = ChapterDetector()
        start = self.start
        page_num = 0
        while start < self.end:
            page_num += 1
            end = self.find_nearest_page_end(start)

            # Check for chapters near the end of the current page segment
            chapter_search_text = self.text[start + self.min_length : start + self.max_length]
            if chapters := chapter_detector.get_chapters(chapter_search_text):
                # Find the chapter position that is nearest to the target page size
                target_position = start + self.target_length
                # Use the position field from ChapterMatch to find the nearest chapter
                nearest_chapter_idx = min(
                    range(len(chapters)),
                    key=lambda i: abs(
                        (start + self.min_length + chapters[i].position) - target_position,
                    ),
                )
                # Set end to the start of the nearest chapter
                end = start + self.min_length + chapters[nearest_chapter_idx].position

            yield self.normalize(self.text[start:end])
            assert end > start
            start = end

    def normalize(self, text: str) -> str:
        text = re.sub(r"\r", "", text)
        return re.sub(r"[ \t]+", " ", text)

    def find_nearest_page_end_match(
        self,
        page_start_index: int,
        pattern: re.Pattern[str],
    ) -> int | None:
        """Find the nearest regex match around expected end of page.

        In no such match in the vicinity, return None.
        Calculate the vicinity based on the expected PAGE_LENGTH_TARGET
        and PAGE_LENGTH_ERROR_TOLERANCE.
        """
        end_pos = min(
            page_start_index + int(self.max_length),
            self.end,
        )
        start_pos = max(
            page_start_index + int(self.min_length),
            self.start,
        )
        ends = [match.end() for match in pattern.finditer(self.text, start_pos, end_pos)]
        return (
            min(ends, key=lambda x: abs(x - (page_start_index + self.target_length)))
            if ends
            else None
        )

    def find_nearest_page_end(self, page_start_index: int) -> int:
        """Find the nearest page end."""
        patterns = [  # sorted by priority
            re.compile(r"(\r?\n|\u2028|\u2029)(\s*(\r?\n|\u2028|\u2029))+"),  # Paragraph end
            re.compile(r"(\r?\n|\u2028|\u2029)"),  # Line end
            re.compile(r"[^\s.!?]*\w[^\s.!?]*[.!?]\s"),  # Sentence end
            re.compile(r"\w+\b"),  # Word end
        ]

        for pattern in patterns:
            if nearest_page_end := self.find_nearest_page_end_match(
                page_start_index,
                pattern,
            ):
                return self.handle_p_tag_split(page_start_index, nearest_page_end)

        # If no suitable end found, return the maximum allowed length
        return min(page_start_index + self.end, page_start_index + self.target_length)

    def handle_p_tag_split(self, page_start_index: int, nearest_page_end: int) -> int:
        """Find the position of the last closing </p> tag before the split."""
        # todo: remove that - we work with with plain text here
        last_open_p_tag_pos = self.text.find("<p", page_start_index, nearest_page_end)
        last_close_p_tag_pos = self.text.rfind("</p>", page_start_index, nearest_page_end)

        if last_open_p_tag_pos != -1 and (
            last_close_p_tag_pos == -1 or last_close_p_tag_pos < last_open_p_tag_pos
        ):
            # Split <p> between pages
            self.text = f"{self.text[:nearest_page_end]}</p><p>{self.text[nearest_page_end:]}"
            nearest_page_end += len("</p>")

        return nearest_page_end
