"""Detect headings."""

import logging
import re
from typing import NamedTuple

MIN_CHAPTER_DISTANCE = 20


log = logging.getLogger()


class Chapter(NamedTuple):
    """Chapter information."""

    title: str
    position: int


class ChapterDetector:
    """Detect chapters in pure text to create a Table of Contents."""

    def __init__(self, min_chapter_distance: int = MIN_CHAPTER_DISTANCE) -> None:
        """
        min_chapter_distance: Minimum character distance required between chapters.
            Chapter signatures detected within this threshold from previously detected chapters
            will be ignored. Default is 20 characters.
        """
        self.min_chapter_distance = min_chapter_distance

    def get_chapters(self, page_text: str) -> list[Chapter]:
        """Detect chapter headings in the text.

        Return a list of Chapter objects containing:
        - title: The chapter title
        - position: The character position in the text where the chapter starts
        """
        patterns = self.prepare_chapter_patterns()
        chapters: list[Chapter] = []
        for pattern in patterns:
            for match in pattern.finditer(page_text):
                title = re.sub(r"([\s\r\t\n]|<br/>)+", " ", match.group("title")).strip()
                position = match.start("title")
                chapters.append(
                    Chapter(
                        title=title,
                        position=position,
                    ),
                )
        return self._deduplicate_chapters(chapters)

    def _deduplicate_chapters(self, chapters: list[Chapter]) -> list[Chapter]:
        """Deduplicate chapters based on position and title."""
        if not chapters:
            return []
        sorted_chapters = sorted(chapters, key=lambda c: c.position)

        deduplicated: list[Chapter] = []
        seen_titles = set()

        for chapter in sorted_chapters:
            if chapter.title in seen_titles:
                continue
            if (
                not deduplicated
                or abs(deduplicated[-1].position - chapter.position) >= self.min_chapter_distance
            ):
                deduplicated.append(chapter)
                seen_titles.add(chapter.title)
        return deduplicated

    def prepare_chapter_patterns(self) -> list[re.Pattern[str]]:  # pylint: disable=too-many-locals
        """Prepare regex patterns for detecting chapter headings."""
        # Form 1: Chapter I, Chapter 1, Chapter the First, CHAPTER 1
        # Ways of enumerating chapters, e.g.
        space = r"[ \t]"
        line_sep = rf"{space}*(\r?\n|\u2028|\u2029|{space}*<br\/>{space}*)"
        arabic_numerals = r"\d+"
        roman_numerals = "(?=[MDCLXVI])M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})"
        number_words_by_tens_list = [
            "twenty",
            "thirty",
            "forty",
            "fifty",
            "sixty",
            "seventy",
            "eighty",
            "ninety",
        ]
        number_words_list = [
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        ] + number_words_by_tens_list
        number_word = "(" + "|".join(number_words_list) + ")"
        ordinal_number_words_by_tens_list = [
            "twentieth",
            "thirtieth",
            "fortieth",
            "fiftieth",
            "sixtieth",
            "seventieth",
            "eightieth",
            "ninetieth",
        ] + number_words_by_tens_list
        ordinal_number_words_list = (
            [
                "first",
                "second",
                "third",
                "fourth",
                "fifth",
                "sixth",
                "seventh",
                "eighth",
                "ninth",
                "twelfth",
                "last",
            ]
            + [f"{numberWord}th" for numberWord in number_words_list]
        ) + ordinal_number_words_by_tens_list
        ordinal_word = "(the )?(" + "|".join(ordinal_number_words_list) + ")"
        enumerators = rf"({arabic_numerals}|{roman_numerals}|{number_word}|{ordinal_word})"
        chapter_name = r"[\w \t '`\"\.’\?!:\/-]{1,120}"
        name_line = rf"{line_sep}{space}*{chapter_name}{space}*"

        templ_key_word = (
            rf"(chapter|glava|глава|часть|том){space}+"
            rf"({enumerators}(\.|{space}){space}*)?({space}*{chapter_name})?({name_line})?"
        )
        templ_numbered = (
            rf"({arabic_numerals}|{roman_numerals})\.{space}*({chapter_name})?({name_line})?"
        )
        templ_numbered_dbl_empty_line = (
            rf"({arabic_numerals}|{roman_numerals})"
            rf"(\.|{space}){space}*({chapter_name})?({name_line})?{line_sep}"
        )
        prefix = rf"({line_sep}{line_sep}|\A)"
        return [
            re.compile(
                rf"{prefix}(?P<title>{templ_key_word}){line_sep}{line_sep}",
                re.IGNORECASE,
            ),
            re.compile(
                rf"{prefix}(?P<title>{templ_numbered}){line_sep}{line_sep}",
                re.IGNORECASE,
            ),
            re.compile(
                rf"{prefix}(?P<title>{templ_numbered_dbl_empty_line}){line_sep}{line_sep}",
                re.IGNORECASE,
            ),
        ]
