from ..base import ImmichBaseClient
import os
try:
    from tqdm import tqdm
except ImportError:
    class tqdm:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def update(self, *args): pass

class AssetsMixin(ImmichBaseClient):
    """
    Mixin for Assets related endpoints, handling listing, downloading, and uploading.
    """
    def list_assets(self, **kwargs):
        """
        List assets based on metadata filters.

        Note: The standard way for full library list in v2.x is through search/metadata 
        with empty query as it respects API key restrictions better.

        Args:
            **kwargs: Filtering parameters (e.g., isFavorite, type).

        Returns:
            list: A list of asset data dictionaries.
        """
        return self.post("search/metadata", json=kwargs).get('assets', {}).get('items', [])

    def get_asset_info(self, asset_id):
        """
        Get metadata for a specific asset.

        Args:
            asset_id (str): The UUID of the asset.

        Returns:
            dict: Asset metadata.
        """
        return self.get(f"assets/{asset_id}")

    def update_asset(self, asset_id, **kwargs):
        """
        Update asset metadata.

        Args:
            asset_id (str): The UUID of the asset.
            **kwargs: Metadata fields to update (e.g., isFavorite, isArchived, description).

        Returns:
            dict: The updated asset data.
        """
        return self.put(f"assets/{asset_id}", json=kwargs)

    def delete_assets(self, ids):
        """
        Delete multiple assets.

        Args:
            ids (list): List of asset UUIDs to delete.

        Returns:
            bool: True if deletion was successful (204 No Content).
        """
        return self.delete("assets", json={"ids": ids})

    def download_asset(self, asset_id, output_path=None, stream=True):
        """
        Download high-quality/original asset.

        Args:
            asset_id (str): The UUID of the asset.
            output_path (str, optional): Local path to save the file. If None, returns the response object.
            stream (bool): Whether to stream the download. Defaults to True.

        Returns:
            bool | requests.Response: True if saved to file, or the Response object if no path provided.
        """
        response = self.get(f"assets/{asset_id}/original", stream=stream)
        if not output_path:
            return response
        
        # If output_path is provided, handle the streaming save
        try:
            total_size = int(response.headers.get('content-length', 0))
            with open(output_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(output_path)) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            return True
        except Exception as e:
            print(f"Error downloading asset {asset_id}: {e}")
            return False

    def view_asset(self, asset_id, size="preview", edited=False):
        """
        Retrieve thumbnail/preview for an asset.

        Args:
            asset_id (str): The UUID of the asset.
            size (str): Size of the thumbnail ('preview', 'thumbnail', 'base').
            edited (bool): Whether to retrieve the edited version if available.

        Returns:
            requests.Response: Streaming response containing image data.
        """
        params = {"size": size, "edited": edited}
        return self.get(f"assets/{asset_id}/thumbnail", params=params, stream=True)

    def upload_asset(self, file_path, **kwargs):
        """
        Upload a new asset to the server.

        Args:
            file_path (str): Local path to the file to upload.
            **kwargs: Optional metadata (deviceAssetId, deviceId, fileCreatedAt, isFavorite, etc.).

        Returns:
            dict: The created asset metadata.
        """
        # This usually requires multipart/form-data with 'assetData' key
        with open(file_path, 'rb') as f:
            files = {'assetData': f}
            data = kwargs
            return self.post("assets", files=files, data=data)
