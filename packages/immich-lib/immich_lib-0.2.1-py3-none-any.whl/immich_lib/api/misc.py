from ..base import ImmichBaseClient

class MiscellaneousMixin(ImmichBaseClient):
    """
    Mixin for various API categories including Timeline, API Keys, and Library management.
    """
    # Timeline
    def get_timeline(self, **kwargs):
        """
        Retrieve the asset timeline, grouped by buckets.

        Args:
            **kwargs: Timeline grouping and filtering options.

        Returns:
            list: List of timeline buckets.
        """
        return self.get("timeline", params=kwargs)

    def get_timeline_buckets(self, **kwargs):
        """
        Retrieve specific timeline buckets based on criteria.

        Args:
            **kwargs: Bucket filtering options.

        Returns:
            list: List of matching timeline buckets.
        """
        return self.get("timeline/buckets", params=kwargs)

    # API Keys
    def list_api_keys(self):
        """
        List all API keys associated with the current user.

        Returns:
            list: List of API key metadata (excluding the actual key).
        """
        return self.get("api-keys")

    def create_api_key(self, name):
        """
        Create a new API key for the current user.

        Args:
            name (str): A descriptive name for the API key.

        Returns:
            dict: The newly created API key metadata (including the secret key).
        """
        return self.post("api-keys", json={"name": name})

    def delete_api_key(self, key_id):
        """
        Delete a specific API key.

        Args:
            key_id (str): The UUID of the API key to delete.

        Returns:
            bool: True if deletion was successful (204 No Content).
        """
        return self.delete(f"api-keys/{key_id}")

    # Library
    def get_library_info(self):
        """
        Get overall library statistics and repository information.

        Returns:
            dict: Library info and statistics.
        """
        return self.get("library")

    def cleanup_library(self):
        """
        Trigger a background cleanup of the library (e.g., removing unreferenced files).

        Returns:
            bool: True if cleanup was successfully triggered (204 No Content).
        """
        return self.post("library/cleanup")
