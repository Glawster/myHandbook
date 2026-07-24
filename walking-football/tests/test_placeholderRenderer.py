"""Tests for XML-aware placeholder replacement."""

from lxml import etree

from scripts.placeholderRenderer import TEXT_NAMESPACE, placeholdersFind, placeholdersRender

_OFFICE = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"


def _document(body: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<office:document-content xmlns:office="{_OFFICE}" '
        f'xmlns:text="{TEXT_NAMESPACE}">'
        f"<office:body><office:text>{body}</office:text></office:body>"
        "</office:document-content>"
    ).encode()


def test_placeholdersRenderAcrossStyledSpans() -> None:
    content = _document(
        '<text:p text:style-name="Body">'
        '<text:span text:style-name="Strong">{{session</text:span>'
        "<text:span>Title}}</text:span>"
        "</text:p>"
    )

    rendered = placeholdersRender(content, {"sessionTitle": "First Touch & Movement"})
    tree = etree.fromstring(rendered)

    assert "".join(tree.itertext()) == "First Touch & Movement"
    assert b'text:style-name="Strong"' in rendered
    assert placeholdersFind(rendered) == set()


def test_placeholdersRenderSequenceAsOdfLineBreaks() -> None:
    content = _document("<text:p>{{equipment}}</text:p>")

    rendered = placeholdersRender(content, {"equipment": "Balls\nBibs\nCones"})
    tree = etree.fromstring(rendered)
    lineBreaks = tree.xpath("//text:line-break", namespaces={"text": TEXT_NAMESPACE})

    assert len(lineBreaks) == 2
    assert "".join(tree.itertext()) == "BallsBibsCones"


def test_placeholdersRenderMultipleMatchesRightToLeft() -> None:
    content = _document("<text:p>{{theme}} — {{keyPhrase}}</text:p>")

    rendered = placeholdersRender(
        content, {"theme": "Passing", "keyPhrase": "Pass. Move."}
    )

    assert "Passing — Pass. Move.".encode() in rendered
