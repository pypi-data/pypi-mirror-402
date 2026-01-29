from ..base import ImmichBaseClient

class AlbumsMixin(ImmichBaseClient):
    """
    Mixin for Albums related endpoints, handling album lifecycle and sharing.
    """
    def list_albums(self, shared=None):
        """
        List albums. If shared is None, merges owned and shared albums.

        Args:
            shared (bool, optional): Filter by shared status. 
                                     True for shared, False for owned, None for all.

        Returns:
            list: A list of album data dictionaries.
        """
        if shared is not None:
            params = {"shared": "true" if shared else "false"}
            return self.get("albums", params=params)
        
        # Merge owned and shared by default
        owned = self.get("albums", params={"shared": "false"})
        shared_list = self.get("albums", params={"shared": "true"})
        
        album_map = {a['id']: a for a in owned}
        for a in shared_list:
            if a['id'] not in album_map:
                album_map[a['id']] = a
        return list(album_map.values())

    def create_album(self, album_name, asset_ids=None, description=None):
        """
        Create a new album.

        Args:
            album_name (str): The name of the new album.
            asset_ids (list, optional): Initial list of asset UUIDs to include.
            description (str, optional): A description for the album.

        Returns:
            dict: The created album metadata.
        """
        data = {"albumName": album_name}
        if asset_ids: data["assetIds"] = asset_ids
        if description: data["description"] = description
        return self.post("albums", json=data)

    def get_album(self, album_id):
        """
        Get details of a specific album.

        Args:
            album_id (str): The UUID of the album.

        Returns:
            dict: Album metadata including the list of assets.
        """
        return self.get(f"albums/{album_id}")

    def update_album(self, album_id, album_name=None, description=None, album_thumbnail_asset_id=None):
        """
        Update album details.

        Args:
            album_id (str): The UUID of the album.
            album_name (str, optional): New name for the album.
            description (str, optional): New description.
            album_thumbnail_asset_id (str, optional): UUID of the asset to use as cover.

        Returns:
            dict: The updated album metadata.
        """
        data = {}
        if album_name: data["albumName"] = album_name
        if description: data["description"] = description
        if album_thumbnail_asset_id: data["albumThumbnailAssetId"] = album_thumbnail_asset_id
        return self.patch(f"albums/{album_id}", json=data)

    def delete_album(self, album_id):
        """
        Delete an album.

        Args:
            album_id (str): The UUID of the album to delete.

        Returns:
            bool: True if deletion was successful (204 No Content).
        """
        return self.delete(f"albums/{album_id}")

    def add_assets_to_album(self, album_id, asset_ids):
        """
        Add multiple assets to an album.

        Args:
            album_id (str): The UUID of the album.
            asset_ids (list): List of asset UUIDs to add.

        Returns:
            list: Results of the addition for each asset.
        """
        return self.put(f"albums/{album_id}/assets", json={"ids": asset_ids})

    def remove_assets_from_album(self, album_id, asset_ids):
        """
        Remove multiple assets from an album.

        Args:
            album_id (str): The UUID of the album.
            asset_ids (list): List of asset UUIDs to remove.

        Returns:
            bool: True if removal was successful (204 No Content).
        """
        return self.delete(f"albums/{album_id}/assets", json={"ids": asset_ids})

    def add_users_to_album(self, album_id, users):
        """
        Share an album with multiple users.

        Args:
            album_id (str): The UUID of the album.
            users (list): List of dictionaries containing 'userId' and 'role' ('editor' or 'viewer').

        Returns:
            dict: The updated album sharing metadata.
        """
        return self.put(f"albums/{album_id}/users", json={"users": users})

    def remove_user_from_album(self, album_id, user_id):
        """
        Remove a user from an album. 

        Args:
            album_id (str): The UUID of the album.
            user_id (str): The UUID of the user. Use 'me' to leave a shared album.

        Returns:
            bool: True if successful (204 No Content).
        """
        return self.delete(f"albums/{album_id}/user/{user_id}")

    def find_album(self, identifier):
        """
        Find an album by ID or name (case-insensitive).

        Args:
            identifier (str): The UUID or name of the album to find.

        Returns:
            dict | None: The album metadata if found, else None.
        """
        # Try both owned and shared
        albums = self.list_albums(shared=False)
        shared_albums = self.list_albums(shared=True)
        
        # Merge unique
        album_map = {a['id']: a for a in albums}
        for a in shared_albums:
            if a['id'] not in album_map:
                album_map[a['id']] = a
        
        for album in album_map.values():
            if album['id'] == identifier or album.get('albumName', '').lower() == identifier.lower():
                return album
        return None
