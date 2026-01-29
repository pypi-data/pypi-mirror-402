from ..base import ImmichBaseClient

class TagsMixin(ImmichBaseClient):
    """
    Mixin for Tags related endpoints, managing custom tags and asset assignments.
    """
    def list_tags(self):
        """
        Get all tags created by the user.

        Returns:
            list: List of tag metadata.
        """
        return self.get("tags")

    def create_tag(self, name, type="TEXT"):
        """
        Create a new custom tag.

        Args:
            name (str): The name of the tag.
            type (str): The type of tag. Defaults to "TEXT".

        Returns:
            dict: The created tag metadata.
        """
        return self.post("tags", json={"name": name, "type": type})

    def get_tag(self, tag_id):
        """
        Get metadata for a specific tag.

        Args:
            tag_id (str): The UUID of the tag.

        Returns:
            dict: Tag metadata.
        """
        return self.get(f"tags/{tag_id}")

    def update_tag(self, tag_id, name):
        """
        Update a tag's name.

        Args:
            tag_id (str): The UUID of the tag.
            name (str): The new name for the tag.

        Returns:
            dict: The updated tag metadata.
        """
        return self.patch(f"tags/{tag_id}", json={"name": name})

    def delete_tag(self, tag_id):
        """
        Delete a tag.

        Args:
            tag_id (str): The UUID of the tag to delete.

        Returns:
            bool: True if deletion was successful (204 No Content).
        """
        return self.delete(f"tags/{tag_id}")

    def tag_assets(self, tag_id, asset_ids):
        """
        Assign a tag to multiple assets.

        Args:
            tag_id (str): The UUID of the tag.
            asset_ids (list): List of asset UUIDs to tag.

        Returns:
            list: Result details for each asset assignment.
        """
        return self.put(f"tags/{tag_id}/assets", json={"ids": asset_ids})

    def untag_assets(self, tag_id, asset_ids):
        """
        Remove a tag from multiple assets.

        Args:
            tag_id (str): The UUID of the tag.
            asset_ids (list): List of asset UUIDs to untag.

        Returns:
            bool: True if removal was successful (204 No Content).
        """
        return self.delete(f"tags/{tag_id}/assets", json={"ids": asset_ids})
