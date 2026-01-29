import allure
import pytest
from lxml import html

from pagesmith import parse_partial_html
from pagesmith import etree_to_str
from pagesmith.parser import FAKE_ROOT


@allure.epic("HTML parser")
@pytest.mark.parametrize("root_tag", ["span", "div", "sup"])
def test_parser_multi_root_tags(root_tag):
    e = parse_partial_html(f"<{root_tag}>1<p>7</p></{root_tag}>3<{root_tag}>2</{root_tag}>4")
    assert etree_to_str(e) == f"<{root_tag}>1<p>7</p></{root_tag}>3<{root_tag}>2</{root_tag}>4"


@allure.epic("HTML parser")
def test_parser_p_tags():
    """Lxml fix the nested <p> tags."""
    e = parse_partial_html("<p>1<p>7</p></p>3<p>2</p>4")
    assert etree_to_str(e) == "<p>1</p><p>7</p>3<p>2</p>4"


@allure.epic("HTML parser")
def test_parser_ignore_multiple_html():
    e = parse_partial_html("1<html>2<p>3</p>4</html>5<html>6<html>7</html>8</html>9")
    assert etree_to_str(e) == "12<p>3</p>456789"


@allure.epic("HTML parser")
def test_parser_respect_root_html():
    e = parse_partial_html("<html>2<p>3</p>4</html>")
    assert etree_to_str(e) == "<html>2<p>3</p>4</html>"


@allure.epic("HTML parser")
def test_parser_respect_single_html():
    e = parse_partial_html("""<!DOCTYPE html>
<!--
You know you could be getting paid to poke around in our code?
We're hiring designers and developers to work in Amsterdam:
https://careers.booking.com/
-->
<!-- wdot-802 -->
<script type="text/javascript" nonce="98fK0yasXFqd7nj"/>
<html>2<p>3</p>4</html>
<script>??</script>""")
    result = etree_to_str(e)
    expected = '<script type="text/javascript" nonce="98fK0yasXFqd7nj"></script> <html>2<p>3</p>4</html> <script>??</script>'
    # Remove leading/trailing whitespace for comparison
    assert result.strip() == expected.strip()


@allure.epic("HTML parser")
def test_parser_text():
    e = parse_partial_html("12<p>7</p>34")
    assert etree_to_str(e) == "12<p>7</p>34"


@allure.epic("HTML parser")
class TestMalformedHTML:
    """Test cases for malformed HTML that might come from internet sites."""

    def test_unclosed_tags(self):
        """Test handling of unclosed tags."""
        e = parse_partial_html("<div>content<p>paragraph<span>text")
        result = etree_to_str(e)
        assert "<div>" in result
        assert "<p>" in result
        assert "<span>" in result
        assert "content" in result
        assert "paragraph" in result
        assert "text" in result

    def test_mismatched_tags(self):
        """Test handling of mismatched opening/closing tags."""
        e = parse_partial_html("<div>content</span><p>text</div>")
        result = etree_to_str(e)
        assert "content" in result
        assert "text" in result

    def test_invalid_tag_names(self):
        """Test handling of invalid tag names."""
        e = parse_partial_html("<123>invalid<456>tags</789>content")
        result = etree_to_str(e)
        assert "invalid" in result
        assert "tags" in result
        assert "content" in result

    def test_broken_attributes(self):
        """Test handling of broken/malformed attributes."""
        e = parse_partial_html('<div class="test onclick="alert() id=broken>content</div>')
        result = etree_to_str(e)
        assert "content" in result
        assert "<div" in result

    def test_unescaped_content(self):
        """Test handling of unescaped HTML entities and characters."""
        e = parse_partial_html("<div>Price: $100 & tax < 5% > discount</div>")
        result = etree_to_str(e)
        assert "Price:" in result
        assert "$100" in result

    def test_mixed_quotes_in_attributes(self):
        """Test handling of mixed single/double quotes in attributes."""
        e = parse_partial_html(
            """<div class='test" id="broken' onclick='alert("hi")'>content</div>"""
        )
        result = etree_to_str(e)
        assert "content" in result
        assert "<div" in result


@allure.epic("HTML parser")
class TestScriptAndStyleTags:
    """Test cases for script and style tags with various content."""

    def test_script_with_html_content(self):
        """Test script tags containing HTML-like content."""
        e = parse_partial_html('<script>document.write("<div>hello</div>");</script><p>after</p>')
        result = etree_to_str(e)
        assert "<script>" in result
        assert "<p>after</p>" in result
        assert "document.write" in result

    def test_style_with_selectors(self):
        """Test style tags with CSS selectors that look like HTML."""
        e = parse_partial_html("<style>div > p { color: red; }</style><div>content</div>")
        result = etree_to_str(e)
        assert "<style>" in result
        assert "<div>content</div>" in result
        assert "color: red" in result

    def test_script_with_closing_tags(self):
        """Test script containing closing script tags."""
        e = parse_partial_html('<script>var x = "</script>"; alert(x);</script><p>after</p>')
        result = etree_to_str(e)
        assert "<p>after</p>" in result


@allure.epic("HTML parser")
class TestSpecialCharacters:
    """Test cases for special characters and encoding issues."""

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        e = parse_partial_html("<div>🌟 Unicode ñ ü ß content 中文</div>")
        result = etree_to_str(e)
        assert "🌟" in result
        assert "ñ" in result
        assert "中文" in result

    def test_null_bytes(self):
        """Test handling of null bytes."""
        e = parse_partial_html("<div>content\x00with\x00nulls</div>")
        result = etree_to_str(e)
        assert "content" in result
        assert "with" in result
        assert "nulls" in result

    def test_control_characters(self):
        """Test handling of control characters."""
        e = parse_partial_html("<div>content\twith\ncontrol\rchars</div>")
        result = etree_to_str(e)
        assert "content" in result
        assert "with" in result
        assert "control" in result
        assert "chars" in result


@allure.epic("HTML parser")
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_input(self):
        """Test empty input."""
        e = parse_partial_html("")
        result = etree_to_str(e)
        assert result == ""

    def test_whitespace_only(self):
        """Test whitespace-only input."""
        e = parse_partial_html("   \n\t  ")
        result = etree_to_str(e)
        assert result.strip() == ""

    def test_plain_text_only(self):
        """Test plain text without any HTML tags."""
        e = parse_partial_html("Just plain text content")
        result = etree_to_str(e)
        assert "Just plain text content" in result

    def test_very_long_content(self):
        """Test handling of very long content."""
        long_text = "x" * 10000
        e = parse_partial_html(f"<div>{long_text}</div>")
        result = etree_to_str(e)
        assert long_text in result
        assert "<div>" in result

    def test_deeply_nested_tags(self):
        """Test deeply nested tag structure."""
        nested_html = "<div>" * 50 + "content" + "</div>" * 50
        e = parse_partial_html(nested_html)
        result = etree_to_str(e)
        assert "content" in result
        assert result.count("<div>") > 10  # Some nesting preserved

    def test_single_angle_brackets(self):
        """Test content with single angle brackets."""
        e = parse_partial_html("Price < 100 and > 50")
        result = etree_to_str(e)
        assert "Price" in result
        assert "100" in result
        assert "50" in result

    def test_incomplete_tags_at_boundaries(self):
        """Test incomplete tags at the beginning and end."""
        e = parse_partial_html("iv>content<p>text</p>incomplete<sp")
        result = etree_to_str(e)
        assert "content" in result
        assert "<p>text</p>" in result
        assert "incomplete" in result


@allure.epic("HTML parser")
class TestRealWorldScenarios:
    """Test cases based on real-world HTML scenarios from web scraping."""

    def test_social_media_embed(self):
        """Test social media embed-like content."""
        html = """
        <div class="tweet">
            <p>Check out this <a href="http://example.com">link</a> & more!</p>
            <div class="metadata">
                <span class="author">@user</span>
                <span class="date">2024-01-01</span>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "Check out this" in result
        assert "@user" in result
        assert "2024-01-01" in result

    def test_malformed_list(self):
        """Test malformed list structure."""
        html = """
        <ul>
            <li>Item 1
            <li>Item 2</li>
            Item 3 without li
            <li>Item 4
        </ul>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result
        assert "Item 4" in result

    def test_form_with_missing_attributes(self):
        """Test form elements with missing or malformed attributes."""
        html = """
        <form action= method>
            <input type="text" name="username" value=test>
            <input type=password name=pwd>
            <button type=submit>Submit
        </form>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "<form" in result
        assert "username" in result
        assert "Submit" in result

    def test_table_with_mixed_structure(self):
        """Test table with mixed/incomplete structure."""
        html = """
        <table>
            <tr><td>Cell 1<td>Cell 2</tr>
            <tr><td>Cell 3</td>
            <td>Cell 4</td></tr>
            <td>Orphaned cell</td>
        </table>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "Cell 1" in result
        assert "Cell 2" in result
        assert "Cell 3" in result
        assert "Cell 4" in result
        assert "Orphaned cell" in result

    def test_mixed_content_with_broken_encoding(self):
        """Test content that might have encoding issues."""
        html = '<div>Price: â‚¬100 • Bullet â€" dash</div>'
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "Price:" in result
        assert "100" in result

    def test_xml_like_tags_in_html(self):
        """Test XML-like custom tags mixed with HTML."""
        html = """
        <div>
            <custom:tag attribute="value">Custom content</custom:tag>
            <regular-tag>Regular</regular-tag>
            <self-closing-tag/>
            <p>Normal HTML</p>
        </div>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "Custom content" in result
        assert "Regular" in result
        assert "Normal HTML" in result


@allure.epic("HTML parser")
class TestCommentHandling:
    """Test various comment scenarios."""

    def test_broken_comments(self):
        """Test handling of broken/incomplete comments."""
        e = parse_partial_html("<!-- broken comment <div>content</div> <!-- another comment -->")
        result = etree_to_str(e)
        assert "<div>content</div>" in result

    def test_nested_comments(self):
        """Test nested comment-like structures."""
        e = parse_partial_html("<!-- outer <!-- inner --> still comment --> <p>visible</p>")
        result = etree_to_str(e)
        assert "<p>visible</p>" in result

    def test_comment_with_html_content(self):
        """Test comments containing HTML-like content."""
        e = parse_partial_html("<!-- <script>alert('xss')</script> --><div>safe</div>")
        result = etree_to_str(e)
        assert "<div>safe</div>" in result
        assert "alert" not in result


@allure.epic("HTML parser")
class TestCDATAHandling:
    """Test CDATA section handling."""

    def test_cdata_sections(self):
        """Test handling of CDATA sections."""
        html = """
        <div>
            <![CDATA[
                Some <raw> content & entities
            ]]>
            <p>Normal content</p>
        </div>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "<p>Normal content</p>" in result

    def test_malformed_cdata(self):
        """Test malformed CDATA sections."""
        e = parse_partial_html("<div><![CDATA[ broken cdata <p>content</p>")
        result = etree_to_str(e)
        # lxml ignore all in CDATA till closing ">" and ignore unpaired </p>, restore unclosed <div>
        assert "<div>content</div>" == result


@allure.epic("HTML parser")
class TestDoctypeHandling:
    """Test DOCTYPE declaration handling."""

    def test_multiple_doctypes(self):
        """Test multiple DOCTYPE declarations."""
        html = """
        <!DOCTYPE html>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0//EN">
        <div>content</div>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "<div>content</div>" in result

    def test_malformed_doctype(self):
        """Test malformed DOCTYPE declarations."""
        e = parse_partial_html("<!DOCTYPE broken><div>content</div>")
        result = etree_to_str(e)
        assert "<div>content</div>" in result


@allure.epic("HTML parser")
class TestEtreeFunctionality:
    """Test that the parsed result is a functional etree with proper structure."""

    def test_etree_element_properties(self):
        """Test that returned object has proper etree Element properties."""
        e = parse_partial_html("<div class='test' id='main'><p>content</p></div>")

        # Should be a proper etree Element
        assert hasattr(e, "tag")
        assert hasattr(e, "attrib")
        assert hasattr(e, "text")
        assert hasattr(e, "tail")
        assert hasattr(e, "__len__")
        assert hasattr(e, "__iter__")

        # Get the actual div element (skip root wrapper if present)
        if e.tag == FAKE_ROOT and len(e) == 1:
            div_elem = e[0]
        else:
            div_elem = e

        # Should support etree operations
        assert div_elem.tag == "div"
        assert div_elem.attrib["class"] == "test"
        assert div_elem.attrib["id"] == "main"
        assert len(div_elem) == 1  # One child element

    def test_xpath_functionality(self):
        """Test that XPath queries work on parsed elements."""
        html = """
        <div class="container">
            <p class="intro">Introduction</p>
            <div class="content">
                <span id="highlight">Important text</span>
                <p>More content</p>
            </div>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """
        e = parse_partial_html(html)

        # Test various XPath queries
        assert len(e.xpath(".//p")) >= 2  # At least 2 paragraph elements
        assert len(e.xpath(".//li")) == 2  # Exactly 2 list items
        assert len(e.xpath('.//*[@class="intro"]')) == 1  # Element with class intro
        assert len(e.xpath('.//*[@id="highlight"]')) == 1  # Element with id highlight
        assert e.xpath('.//span[@id="highlight"]/text()')[0] == "Important text"

    def test_element_navigation(self):
        """Test parent/child navigation in the etree."""
        e = parse_partial_html("<div><p><span>text</span></p><ul><li>item</li></ul></div>")

        # Test parent-child relationships
        p_elem = e.xpath(".//p")[0]
        span_elem = e.xpath(".//span")[0]
        li_elem = e.xpath(".//li")[0]

        assert span_elem.getparent() == p_elem
        # p_elem's parent should be div, not the root wrapper
        div_elem = e.xpath(".//div")[0]
        assert p_elem.getparent() == div_elem

        # Test siblings
        children = list(div_elem)
        assert len(children) == 2  # p and ul
        assert children[0].tag == "p"
        assert children[1].tag == "ul"

    def test_text_content_access(self):
        """Test accessing text content through etree methods."""
        e = parse_partial_html("<div>Start <span>middle</span> end</div>")

        # Get the actual div element
        div_elem = e.xpath(".//div")[0]

        # Test direct text access
        assert div_elem.text == "Start "
        span = div_elem[0]
        assert span.text == "middle"
        assert span.tail == " end"

        # Test itertext()
        all_text = "".join(div_elem.itertext())
        assert all_text == "Start middle end"

    def test_attribute_manipulation(self):
        """Test that attributes can be read and modified."""
        e = parse_partial_html('<div class="old" id="test" data-value="123">content</div>')

        # Get the actual div element
        div_elem = e.xpath(".//div")[0]

        # Read attributes
        assert div_elem.get("class") == "old"
        assert div_elem.get("id") == "test"
        assert div_elem.get("data-value") == "123"
        assert div_elem.get("nonexistent") is None

        # Modify attributes
        div_elem.set("class", "new")
        div_elem.set("title", "added")

        assert div_elem.get("class") == "new"
        assert div_elem.get("title") == "added"

        # Test attrib dict
        assert "id" in div_elem.attrib
        assert len(div_elem.attrib) >= 3


@allure.epic("HTML parser")
class TestValidTagParsing:
    """Test that all valid HTML tags are correctly parsed and preserved."""

    def test_common_html_tags(self):
        """Test parsing of common HTML tags."""
        tags_to_test = [
            "div",
            "span",
            "p",
            "a",
            "img",
            "br",
            "hr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "dl",
            "dt",
            "dd",
            "table",
            "tr",
            "td",
            "th",
            "thead",
            "tbody",
            "tfoot",
            "form",
            "input",
            "button",
            "select",
            "option",
            "textarea",
            "strong",
            "em",
            "b",
            "i",
            "u",
            "small",
            "sub",
            "sup",
            "blockquote",
            "pre",
            "code",
            "kbd",
            "samp",
            "var",
        ]

        for tag in tags_to_test:
            html = f"<{tag}>content</{tag}>"
            e = parse_partial_html(html)

            # Check if the root element itself is the tag we're looking for
            if e.tag == tag:
                assert e.tag == tag, f"Root tag should be '{tag}'"
            else:
                # Otherwise find the tag in the tree
                found_elements = e.xpath(f".//{tag}")
                assert len(found_elements) >= 1, f"Tag '{tag}' not found in parsed result"
                assert found_elements[0].tag == tag

    def test_self_closing_tags(self):
        """Test self-closing tags are handled correctly."""
        self_closing_tags = ["br", "hr", "img", "input", "meta", "link", "area", "base", "col"]

        for tag in self_closing_tags:
            html = f"before<{tag}/>after"
            e = parse_partial_html(html)

            # Check if we can find the tag either as root or in tree
            if e.tag == tag:
                found_elements = [e]
            else:
                found_elements = e.xpath(f".//{tag}")
            assert len(found_elements) >= 1, f"Self-closing tag '{tag}' not found"

    def test_tags_with_attributes(self):
        """Test that tags with various attributes are parsed correctly."""
        html = """
        <div class="container" id="main" data-value="test">
            <a href="http://example.com" target="_blank" rel="noopener">Link</a>
            <img src="image.jpg" alt="Description" width="100" height="50"/>
            <input type="text" name="username" value="default" placeholder="Enter name"/>
        </div>
        """
        e = parse_partial_html(html)

        # Find div element (could be root or in tree)
        if e.tag == "div" and e.get("class") == "container":
            div_elem = e
        else:
            div_elements = e.xpath('.//div[@class="container"]')
            assert len(div_elements) > 0, "Container div not found"
            div_elem = div_elements[0]

        # Test div attributes
        assert div_elem.get("id") == "main"
        assert div_elem.get("data-value") == "test"

        # Test anchor attributes
        a_elements = e.xpath(".//a") if e.tag != "a" else [e]
        assert len(a_elements) > 0, "Anchor element not found"
        a_elem = a_elements[0]
        assert a_elem.get("href") == "http://example.com"
        assert a_elem.get("target") == "_blank"
        assert a_elem.get("rel") == "noopener"

        # Test img attributes
        img_elements = e.xpath(".//img") if e.tag != "img" else [e]
        assert len(img_elements) > 0, "Image element not found"
        img_elem = img_elements[0]
        assert img_elem.get("src") == "image.jpg"
        assert img_elem.get("alt") == "Description"
        assert img_elem.get("width") == "100"

        # Test input attributes
        input_elements = e.xpath(".//input") if e.tag != "input" else [e]
        assert len(input_elements) > 0, "Input element not found"
        input_elem = input_elements[0]
        assert input_elem.get("type") == "text"
        assert input_elem.get("name") == "username"
        assert input_elem.get("value") == "default"

    def test_nested_structure_preservation(self):
        """Test that nested tag structures are preserved correctly."""
        html = """
        <article>
            <header>
                <h1>Title</h1>
                <p class="meta">By <strong>Author</strong> on <time>2024-01-01</time></p>
            </header>
            <section class="content">
                <p>First paragraph with <em>emphasis</em> and <a href="#ref">link</a>.</p>
                <blockquote>
                    <p>Quoted text with <cite>citation</cite>.</p>
                </blockquote>
                <ul>
                    <li>First <strong>item</strong></li>
                    <li>Second item with <code>code</code></li>
                </ul>
            </section>
        </article>
        """
        e = parse_partial_html(html)

        # Test overall structure - check if root is article or find it
        if e.tag == "article":
            article_elem = e
        else:
            articles = e.xpath(".//article")
            assert len(articles) > 0, "Article element not found"
            article_elem = articles[0]

        assert article_elem.tag == "article"

        # Find header and section within the article or tree
        headers = article_elem.xpath(".//header") if e.tag != "header" else [e]
        sections = article_elem.xpath(".//section") if e.tag != "section" else [e]

        assert len(headers) >= 1, "Header not found"
        assert len(sections) >= 1, "Section not found"

        # Test nested elements are in correct hierarchy
        h1_elements = e.xpath(".//h1")
        if len(h1_elements) > 0:
            h1 = h1_elements[0]
            assert h1.getparent().tag == "header"
            assert h1.getparent().getparent().tag == "article"

        # Test deeply nested elements
        strong_in_li = e.xpath(".//li/strong")
        if len(strong_in_li) > 0:
            strong_elem = strong_in_li[0]
            assert strong_elem.text == "item"
            assert strong_elem.getparent().tag == "li"
            assert strong_elem.getparent().getparent().tag == "ul"

    def test_mixed_valid_invalid_tags(self):
        """Test parsing when valid and invalid tags are mixed."""
        html = """
        <div class="valid">
            <p>Valid paragraph</p>
            <invalid-tag>Invalid but preserved</invalid-tag>
            <span>Valid span</span>
            <123>Invalid number tag</123>
            <em>Valid emphasis</em>
        </div>
        """
        e = parse_partial_html(html)

        # Valid tags should be parsed correctly - check if root is div or find it
        if e.tag == "div":
            div_elements = [e]
        else:
            div_elements = e.xpath(".//div")
        assert len(div_elements) >= 1, "Div element not found"

        # Check for other valid tags
        p_elements = e.xpath(".//p") if e.tag != "p" else [e]
        span_elements = e.xpath(".//span") if e.tag != "span" else [e]
        em_elements = e.xpath(".//em") if e.tag != "em" else [e]

        assert len(p_elements) >= 1, "P element not found"
        assert len(span_elements) >= 1, "Span element not found"
        assert len(em_elements) >= 1, "Em element not found"

        # Content should be preserved
        result = etree_to_str(e)
        assert "Valid paragraph" in result
        assert "Invalid but preserved" in result
        assert "Valid span" in result
        assert "Valid emphasis" in result

    def test_semantic_html5_tags(self):
        """Test HTML5 semantic tags."""
        html5_tags = [
            "article",
            "aside",
            "details",
            "figcaption",
            "figure",
            "footer",
            "header",
            "main",
            "mark",
            "nav",
            "section",
            "summary",
            "time",
            "audio",
            "video",
            "source",
            "canvas",
        ]

        for tag in html5_tags:
            html = f"<{tag}>HTML5 content</{tag}>"
            e = parse_partial_html(html)

            # Check if root element is the tag or find it in tree
            if e.tag == tag:
                found_elements = [e]
            else:
                found_elements = e.xpath(f".//{tag}")
            assert len(found_elements) >= 1, f"HTML5 tag '{tag}' not found"
            assert "HTML5 content" in etree_to_str(e)


@allure.epic("HTML parser")
class TestEtreeIntegration:
    """Test integration with lxml etree functionality."""

    def test_element_modification(self):
        """Test that parsed elements can be modified like normal etree elements."""
        e = parse_partial_html("<div><p>original</p></div>")

        # Add new elements
        new_span = html.Element("span")
        new_span.text = "added"
        e.append(new_span)

        # Modify existing elements
        p_elem = e.xpath(".//p")[0]
        p_elem.text = "modified"
        p_elem.set("class", "updated")

        result = etree_to_str(e)
        assert "modified" in result
        assert "added" in result
        assert 'class="updated"' in result

    def test_element_removal(self):
        """Test removing elements from parsed tree."""
        e = parse_partial_html("<div><p>keep</p><span>remove</span><em>keep</em></div>")

        # Remove span element
        span_elem = e.xpath(".//span")[0]
        span_elem.getparent().remove(span_elem)

        result = etree_to_str(e)
        assert "keep" in result
        assert "remove" not in result
        assert len(e.xpath(".//span")) == 0

    def test_serialization_options(self):
        """Test different serialization options work correctly."""
        e = parse_partial_html('<div class="test">Content &amp; more</div>')

        # Test HTML serialization (default)
        html_result = html.tostring(e, encoding="unicode", method="html")
        assert "<div" in html_result
        assert 'class="test"' in html_result

        # Test that we can get clean text content
        text_content = "".join(e.itertext())
        assert "Content & more" in text_content or "Content &amp; more" in text_content


@allure.epic("HTML parser")
class TestPreservationBehavior:
    """Test that content is preserved even when parsing fails."""

    def test_preserve_text_when_tags_fail(self):
        """Ensure text content is never lost."""
        malformed_inputs = [
            "<<>>text<<",
            "<>content</>",
            "text < > more text",
            "start<incomplete",
            ">>backwards<<",
        ]

        for html_input in malformed_inputs:
            e = parse_partial_html(html_input)
            result = etree_to_str(e)
            # Check that some meaningful content is preserved
            assert len(result.strip()) > 0, f"Content lost for input: {html_input}"

    def test_preserve_all_text_content(self):
        """Test that all text content is preserved regardless of tag structure."""
        html = "<broken>important</invalid>text<>content</wrong>end"
        e = parse_partial_html(html)
        result = etree_to_str(e)

        expected_texts = ["important", "text", "content", "end"]
        for text in expected_texts:
            assert text in result, f"Text '{text}' was lost during parsing"

    def test_head_tag(self):
        html = "<html><head><title>Test</title></head><body><p>Hello, world!</p></body></html>"
        e = parse_partial_html(html)
        result = etree_to_str(e)
        assert "<head>" in result

    def test_body_tag(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Original Heading</h1>
            <p>Original paragraph.</p>
        </body>
        </html>
        """
        e = parse_partial_html(html)
        result = etree_to_str(e)
        print(result)
        assert "<body>" in result
