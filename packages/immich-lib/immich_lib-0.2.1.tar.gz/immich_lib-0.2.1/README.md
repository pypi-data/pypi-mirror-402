[![Coverage Status](coverage.svg)](coverage.svg)

# Immich Lib

A Python library and CLI tool for interacting with an Immich server.

## Installation

```bash
pip install .
```

## CLI Usage

After installation, you can use the `immich-tool` command:

```bash
immich-tool list-albums
immich-tool download-album "My Album"
```

You can also pass the URL and API key as arguments:

```bash
immich-tool --url http://immich.local:2283 --key YOUR_API_KEY list-albums
```

Or set them in your environment or a `.env` file:

```env
IMMICH_SERVER_URL=http://immich.local:2283
IMMICH_API_KEY=YOUR_API_KEY
```

## Library Usage

```python
from immich_lib import ImmichClient

client = ImmichClient("http://immich.local:2283", "YOUR_API_KEY")
albums = client.list_albums()
for album in albums:
    print(album['albumName'])
```
