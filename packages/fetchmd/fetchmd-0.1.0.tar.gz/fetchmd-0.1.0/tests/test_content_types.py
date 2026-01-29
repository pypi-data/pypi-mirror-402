import respx

from fetchmd import fetchmd


@respx.mock
def test_markdown_passthrough():
    respx.get("https://example.com").respond(
        200,
        headers={"Content-Type": "text/markdown"},
        text="# Hello\n",
    )
    assert fetchmd("https://example.com") == "# Hello\n"


@respx.mock
def test_plaintext_passthrough():
    respx.get("https://example.com").respond(
        200,
        headers={"Content-Type": "text/plain; charset=utf-8"},
        text="hello",
    )
    assert fetchmd("https://example.com") == "hello"


@respx.mock
def test_accept_header_is_set():
    route = respx.get("https://example.com").respond(
        200, headers={"Content-Type": "text/plain"}, text="ok"
    )
    fetchmd("https://example.com")
    assert route.called
    accept = route.calls[0].request.headers.get("Accept")
    assert "text/markdown" in accept
