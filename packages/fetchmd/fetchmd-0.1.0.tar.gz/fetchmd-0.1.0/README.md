# FetchMD

Fetch any web page as clean Markdown.

## Features

- Fetches a URL and returns Markdown (sync, minimal API).
- Prefers Markdown/plain responses via `Accept`, falls back to HTML conversion.
- Extracts main content with readability by default.
- Absolutizes links and images for fetched URLs.
- Supports piping raw HTML via stdin.

## Install

Requires Python >= 3.10.

```bash
uv tool install fetchmd
```

## CLI

```bash
# Run without installing
uv run fetchmd https://example.com

# Install once, then:
fetchmd https://example.com

# Read raw HTML from stdin
curl https://example.com | fetchmd -

# Skip readability, convert full HTML
fetchmd --raw https://example.com
```

## Python API

```python
from fetchmd import fetchmd

md = fetchmd("https://example.com")
```

## Behavior

- `text/markdown` and `text/plain` are returned as-is.
- HTML is cleaned with readability unless `--raw` is used.
- Relative `href` and `src` are converted to absolute URLs for fetched pages.
- When reading from stdin (`-`), there is no base URL, so links remain unchanged.

## Testing

Run tests on a single Python version:

```sh
uv run --python 3.12 --with pytest -- pytest
```

Run the supported-version matrix:

```sh
./scripts/test-matrix.sh
```

Override versions (space-separated):

```sh
PY_VERSIONS="3.10 3.11 3.12 3.13 3.14" ./scripts/test-matrix.sh
```
