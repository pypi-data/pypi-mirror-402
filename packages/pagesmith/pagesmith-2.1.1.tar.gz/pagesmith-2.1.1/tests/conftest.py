import pytest

from pagesmith import ChapterDetector


@pytest.fixture(scope="function", params=["Hello 123 <br/> word/123 123-<word>\n<br/> and last!"])
def sentence_6_words(request):
    return request.param


@pytest.fixture
def complex_book_text():
    """Generate a complex book text with multiple chapters."""
    chapters = [
        "Chapter 1\n\nFirst chapter content.",
        "Chapter 2\n\nSecond chapter with more text.",
        "Chapter 3\n\nThird chapter with even more text.",
        "Chapter 4\n\nFourth and final chapter.",
    ]

    # Add some space between chapters to force page breaks
    padding = "\n\n" + ". " * 500 + "\n\n"
    return padding.join(chapters)


@pytest.fixture(
    scope="function",
    params=[
        "\n\nCHAPTER VII.\nA Mad Tea-Party\n\n",
        "\n\nCHAPTER I\n\n",
        "\n\nCHAPTER Two\n\n",
        "\n\nCHAPTER Third\n\n",
        "\n\nCHAPTER four. FALL\n\n",
        "\n\nCHAPTER twenty two. WINTER\n\n",
        "\n\nCHAPTER last inline\nunderline\n\n",
        "\n\nI. A SCANDAL IN BOHEMIA\n \n",
        "\n\nV.\nПет наранчиних сjеменки\n\n",
    ],
)
def chapter_pattern(request):
    return request.param


@pytest.fixture(
    scope="function",
    params=[
        "\ncorrespondent could be.\n\n",
    ],
)
def wrong_chapter_pattern(request):
    return request.param


@pytest.fixture
def detector():
    """Create a ChapterDetector instance for testing."""
    return ChapterDetector()
