"""Tests for the ChapterDetector class."""


class TestChapterDetector:
    """Test suite for the ChapterDetector class."""

    def test_arabic_numeral_chapter(self, detector):
        """Test detection of chapters with Arabic numerals."""
        text = "\n\nChapter 1. Introduction \n\n"  # space should be stripped
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Chapter 1. Introduction"
        assert result[0].position == 2  # Position after first two newlines

    def test_text_begin(self, detector):
        """Test detection at beginning of text."""
        text = "Chapter 1. Introduction\n\nChapter text\nChapter 2. Not at the beginning\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1  # Only one chapter should be detected
        assert result[0].title == "Chapter 1. Introduction"
        assert result[0].position == 0  # Beginning of the text

    def test_roman_numeral_chapter(self, detector):
        """Test detection of chapters with Roman numerals."""
        text = "\n\nChapter IV. The Battle\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Chapter IV. The Battle"
        assert result[0].position == 2

    def test_word_number_chapter(self, detector):
        """Test detection of chapters with number words."""
        text = "\n\nChapter one: Beginning\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Chapter one: Beginning"
        assert result[0].position == 2

    def test_ordinal_word_chapter(self, detector):
        """Test detection of chapters with ordinal words."""
        text = "\n\nChapter the First - Origins\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Chapter the First - Origins"
        assert result[0].position == 2

    def test_numbered_only_format(self, detector):
        """Test detection of chapters with just a number and period."""
        text = "\n\n1. The Beginning\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "1. The Beginning"
        assert result[0].position == 2

    def test_roman_numbered_only_format(self, detector):
        """Test detection of chapters with just a Roman numeral and period."""
        text = "\n\nXII. The End\n\n"
        result = detector.get_chapters(text)
        assert len(result) == 1
        assert result[0].title == "XII. The End"
        assert result[0].position == 2

    def test_double_empty_line_format(self, detector):
        """Test detection of chapters with double empty lines."""
        text = "\n\n7. Final Chapter\n\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "7. Final Chapter"
        assert result[0].position == 2

    def test_cyrillic_chapter_name(self, detector):
        """Test detection of chapters with Cyrillic names."""
        text = "\n\nГлава 5 Новое начало\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Глава 5 Новое начало"
        assert result[0].position == 2

    def test_chapter_with_br_tag(self, detector):
        """Test detection of chapters with <br/> tags."""
        text = "\n\nChapter 3<br/>The Journey\n\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Chapter 3 The Journey"  # <br/> should be replaced with space
        assert result[0].position == 2

    def test_multiple_chapters_on_page(self, detector):
        """Test detection of multiple chapters on a single page."""
        chapter1 = "\n\nChapter 1. Introduction\n\nLorem ipsum...\n\n"
        chapter2 = "Chapter 2. Development\n\n"
        text = f"{chapter1}{chapter2}"
        result = detector.get_chapters(text)

        assert len(result) == 2
        assert result[0].title == "Chapter 1. Introduction"
        assert result[0].position == 2  # Position after first two newlines

        print(f"Chapter 1 position: {text[result[1].position :]}")
        assert result[1].title == "Chapter 2. Development"
        assert result[1].position == len(chapter1)

    def test_no_chapters_found(self, detector):
        """Test behavior when no chapters are found."""
        text = "This is just regular text with no chapter headings."
        result = detector.get_chapters(text)

        assert len(result) == 0

    def test_whitespace_normalization(self, detector):
        """Test that whitespace is properly normalized in chapter titles."""
        text = "\n\nChapter  6\t \nThe   Final  Battle\n\r\n"
        result = detector.get_chapters(text)

        assert len(result) == 1
        assert result[0].title == "Chapter 6 The Final Battle"  # Whitespace should be normalized
        assert result[0].position == 2

    def test_prepare_chapter_patterns(self, detector):
        """Test that chapter patterns are correctly prepared."""
        patterns = detector.prepare_chapter_patterns()

        assert len(patterns) == 3  # Should return 3 compiled regex patterns
        for pattern in patterns:
            assert hasattr(pattern, "match")  # Verify these are compiled regex patterns
