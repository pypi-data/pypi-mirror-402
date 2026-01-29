from fetchmd import core


def test_absolutize_links_and_images():
    html = """
    <html><body>
      <a href="/docs">Docs</a>
      <img src="images/logo.png" />
    </body></html>
    """
    out = core._absolutize_html(html, base_url="https://example.com/base/")
    assert "https://example.com/docs" in out
    assert "https://example.com/base/images/logo.png" in out


def test_absolutize_form_action():
    html = """
    <html><body>
      <form action="/submit"><button>Go</button></form>
    </body></html>
    """
    out = core._absolutize_html(html, base_url="https://example.com/base/")
    assert "https://example.com/submit" in out
