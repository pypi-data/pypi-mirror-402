import io
import sys

from fetchmd import cli


def test_cli_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("<p>Hello</p>"))
    monkeypatch.setattr(cli, "html_to_markdown", lambda *_args, **_kwargs: "Hello")

    cli.main(["-"])
    out = capsys.readouterr().out
    assert out.strip() == "Hello"


def test_cli_url_calls_fetch(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_fetchmd", lambda *_args, **_kwargs: "OK")

    cli.main(["https://example.com"])
    out = capsys.readouterr().out
    assert out.strip() == "OK"


def test_cli_raw_skips_readability(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("<p>Raw</p>"))
    monkeypatch.setattr(cli, "html_to_markdown", lambda *_args, **_kwargs: "RAW")

    cli.main(["--raw", "-"])
    out = capsys.readouterr().out
    assert out.strip() == "RAW"
