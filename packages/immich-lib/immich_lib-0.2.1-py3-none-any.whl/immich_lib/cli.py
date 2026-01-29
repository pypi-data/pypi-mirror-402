import os
import sys
import argparse
import json
from .client import ImmichClient

# Try to import optional dependency (python-dotenv)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Optional dependency missing, attempt a simple manual check for .env
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        value = value.strip().strip("'").strip('"')
                        os.environ[key.strip()] = value

# Global configuration from environment
IMMICH_SERVER_URL = os.getenv("IMMICH_SERVER_URL")
IMMICH_API_KEY = os.getenv("IMMICH_API_KEY")


def handle_check_auth(client, args):
    """Verify connection and API key validity"""
    info = client.check_auth()
    if info:
        print(
            f"Successfully connected to Immich! Server Info: {json.dumps(info, indent=2)}"
        )
    else:
        print("Authentication failed or connection error.")


def handle_list_albums(client, args):
    """List all accessible albums"""
    albums = client.list_albums()
    if albums:
        print(f"{'ID':<40} | {'Name':<35} | {'Assets'}")
        print("-" * 85)
        for album in albums:
            name = album.get("albumName", "Unknown")
            count = album.get("assetCount", 0)
            print(f"{album['id']:<40} | {name[:35]:<35} | {count}")
    else:
        print("No albums found or error fetching albums.")


def handle_list_assets(client, args):
    """List all accessible assets in the library"""
    assets = client.list_assets()
    if assets:
        print(f"{'ID':<40} | {'File Name':<35} | {'Type'}")
        print("-" * 85)
        for asset in assets:
            name = asset.get("originalFileName", asset.get("id", "Unknown"))
            atype = asset.get("type", "Unknown")
            print(f"{asset['id']:<40} | {name[:35]:<35} | {atype}")
    else:
        print("No assets found or error fetching assets.")


def handle_list_album_assets(client, args):
    """Show assets contained within a specific album"""
    album = client.find_album(args.album_id_or_name)
    if album:
        album_detail = client.get_album(album["id"])
        if album_detail and "assets" in album_detail:
            assets = album_detail["assets"]
            print(f"Assets in album '{album.get('albumName', 'Unknown')}':")
            print(f"{'ID':<40} | {'File Name':<35} | {'Type'}")
            print("-" * 85)
            for asset in assets:
                name = asset.get("originalFileName", asset.get("id", "Unknown"))
                atype = asset.get("type", "Unknown")
                print(f"{asset['id']:<40} | {name[:35]:<35} | {atype}")
        else:
            print(f"No assets found in album '{album.get('albumName', 'Unknown')}'.")
    else:
        print(f"Album '{args.album_id_or_name}' not found.")


def handle_get_metadata(client, args):
    """Retrieve JSON metadata for a specific asset"""
    info = client.get_asset_info(args.asset_id)
    if info:
        print(json.dumps(info, indent=2))
    else:
        print(f"Asset {args.asset_id} not found.")


def handle_download_album(client, args):
    """Download all assets from a specified album"""
    album = client.find_album(args.album_id_or_name)
    if not album:
        print(f"Album '{args.album_id_or_name}' not found.")
        return

    album_detail = client.get_album(album["id"])
    if not album_detail:
        print(
            f"Error: Could not retrieve details for album '{album.get('albumName', 'Unknown')}'."
        )
        return

    assets = album_detail.get("assets", [])
    if not assets:
        print(f"No assets found in album '{album_detail.get('albumName', 'Unknown')}'")
        return

    print(
        f"Downloading {len(assets)} assets from album '{album_detail['albumName']}'..."
    )
    os.makedirs(args.output, exist_ok=True)

    for asset in assets:
        filename = asset.get("originalFileName", f"{asset['id']}.jpg")
        output_path = os.path.join(args.output, filename)
        client.download_asset(asset["id"], output_path)


def handle_download_asset(client, args):
    """Download a single specific asset"""
    info = client.get_asset_info(args.asset_id)
    if not info:
        print("Asset info not available. Authenticating first might help.")
        filename = args.output or f"{args.asset_id}.bin"
    else:
        filename = args.output or info.get("originalFileName", f"{args.asset_id}.jpg")

    client.download_asset(args.asset_id, filename)


def main():
    """
    Main entry point for the Immich CLI tool.
    """
    parser = argparse.ArgumentParser(description="Immich CLI Tool")
    parser.add_argument(
        "--url", help="Immich Server URL (defaults to IMMICH_SERVER_URL env var)"
    )
    parser.add_argument(
        "--key", help="Immich API Key (defaults to IMMICH_API_KEY env var)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # check-auth
    p_check_auth = subparsers.add_parser(
        "check-auth", help="Verify connection and API key validity"
    )
    p_check_auth.set_defaults(func=handle_check_auth)

    # list-albums
    p_list_albums = subparsers.add_parser(
        "list-albums", help="List all accessible albums"
    )
    p_list_albums.set_defaults(func=handle_list_albums)

    # list-assets
    p_list_assets = subparsers.add_parser(
        "list-assets", help="List all accessible assets in the library"
    )
    p_list_assets.set_defaults(func=handle_list_assets)

    # list-album-assets
    p_list_album_assets = subparsers.add_parser(
        "list-album-assets", help="Show assets contained within a specific album"
    )
    p_list_album_assets.add_argument(
        "album_id_or_name", help="UUID or Name of the album"
    )
    p_list_album_assets.set_defaults(func=handle_list_album_assets)

    # get-metadata
    p_get_metadata = subparsers.add_parser(
        "get-metadata", help="Retrieve JSON metadata for a specific asset"
    )
    p_get_metadata.add_argument("asset_id", help="UUID of the asset")
    p_get_metadata.set_defaults(func=handle_get_metadata)

    # download-album
    p_download_album = subparsers.add_parser(
        "download-album", help="Download all assets from a specified album"
    )
    p_download_album.add_argument("album_id_or_name", help="UUID or Name of the album")
    p_download_album.add_argument(
        "--output", "-o", default="downloads", help="Output directory path"
    )
    p_download_album.set_defaults(func=handle_download_album)

    # download-asset
    p_download_asset = subparsers.add_parser(
        "download-asset", help="Download a single specific asset"
    )
    p_download_asset.add_argument("asset_id", help="UUID of the asset")
    p_download_asset.add_argument("--output", "-o", help="Explicit output file path")
    p_download_asset.set_defaults(func=handle_download_asset)

    args = parser.parse_args()

    # Configuration precedence: argument > environment variable
    url = args.url or IMMICH_SERVER_URL
    key = args.key or IMMICH_API_KEY

    if not args.command:
        parser.print_help()
        return

    if not url or not key:
        print(
            "Error: Immich URL and API Key must be provided via environment variables or arguments."
        )
        print(
            "Set IMMICH_SERVER_URL and IMMICH_API_KEY in your environment or a .env file."
        )
        sys.exit(1)

    client = ImmichClient(url, key)

    # Execute the command handler
    if hasattr(args, "func"):
        args.func(client, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
