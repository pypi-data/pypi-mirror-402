"""Core fetch and conversion helpers for fetchmd."""

from __future__ import annotations

import contextlib

import html2text
import httpx
from lxml import html as lxml_html
from readability import Document

ACCEPT_HEADER = (
    "text/markdown, text/plain;q=0.9, text/html;q=0.8, application/xhtml+xml;q=0.8, */*;q=0.7"
)
USER_AGENT = "fetchmd/0.1"


def _extract_readable_html(html: str) -> str:
    doc = Document(html)
    return doc.summary(html_partial=True)


def _convert_html_to_markdown(html: str) -> str:
    h = html2text.HTML2Text()
    h.body_width = 0
    return h.handle(html)


def _absolutize_html(html: str, *, base_url: str | None) -> str:
    if not base_url:
        return html
    tree = lxml_html.fromstring(html)
    tree.make_links_absolute(base_url)
    return lxml_html.tostring(tree, encoding="unicode")


def html_to_markdown(html: str, *, base_url: str | None, raw: bool) -> str:
    """Convert HTML to Markdown, optionally using readability and absolutizing links.

    Returns:
        Markdown string.

    """
    if raw:
        html = _absolutize_html(html, base_url=base_url)
        return _convert_html_to_markdown(html)

    with contextlib.suppress(Exception):
        html = _extract_readable_html(html)

    html = _absolutize_html(html, base_url=base_url)
    return _convert_html_to_markdown(html)


def _fetchmd(url: str, *, raw: bool) -> str:
    headers = {"Accept": ACCEPT_HEADER, "User-Agent": USER_AGENT}
    with httpx.Client(follow_redirects=True, headers=headers, timeout=10.0) as client:
        resp = client.get(url)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type in {"text/markdown", "text/plain"}:
        return resp.text

    html = resp.text
    return html_to_markdown(html, base_url=str(resp.url), raw=raw)


def fetchmd(url: str) -> str:
    """Fetch a URL and return Markdown.

    Returns:
        Markdown string.

    """
    return _fetchmd(url, raw=False)
