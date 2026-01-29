from typing import NoReturn

import respx

from fetchmd import core


@respx.mock
def test_html_uses_readability_by_default(monkeypatch):
    html = "<html><body><article><p>Hello</p></article></body></html>"
    respx.get("https://example.com").respond(200, headers={"Content-Type": "text/html"}, text=html)

    monkeypatch.setattr(
        core, "_extract_readable_html", lambda _html: "<article><p>Hello</p></article>"
    )
    monkeypatch.setattr(core, "_convert_html_to_markdown", lambda _html: "Hello")

    assert core.fetchmd("https://example.com") == "Hello"


@respx.mock
def test_readability_failure_falls_back(monkeypatch):
    html = "<html><body><p>Fallback</p></body></html>"
    respx.get("https://example.com").respond(200, headers={"Content-Type": "text/html"}, text=html)

    def boom(_html) -> NoReturn:
        msg = "bad"
        raise ValueError(msg)

    seen = {}

    def capture(_html) -> str:
        seen["html"] = _html
        return "ok"

    monkeypatch.setattr(core, "_extract_readable_html", boom)
    monkeypatch.setattr(core, "_convert_html_to_markdown", capture)

    assert core.fetchmd("https://example.com") == "ok"
    assert seen["html"] == html


@respx.mock
def test_raw_skips_readability(monkeypatch):
    html = "<html><body><p>Raw</p></body></html>"
    respx.get("https://example.com").respond(200, headers={"Content-Type": "text/html"}, text=html)

    monkeypatch.setattr(
        core,
        "_extract_readable_html",
        lambda _html: (_ for _ in ()).throw(AssertionError("should not call")),
    )
    monkeypatch.setattr(core, "_convert_html_to_markdown", lambda _html: "ok")

    assert core._fetchmd("https://example.com", raw=True) == "ok"
