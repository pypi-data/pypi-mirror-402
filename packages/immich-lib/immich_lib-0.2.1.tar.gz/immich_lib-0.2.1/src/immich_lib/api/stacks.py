from ..base import ImmichBaseClient

class StacksMixin(ImmichBaseClient):
    """
    Mixin for Asset Stacks related endpoints, allowing grouping of similar assets.
    """
    def create_stack(self, primary_asset_id, asset_ids):
        """
        Create a new asset stack.

        Args:
            primary_asset_id (str): The UUID of the asset to be the primary of the stack.
            asset_ids (list): List of asset UUIDs to include in the stack.

        Returns:
            dict: The created stack metadata.
        """
        return self.post("stacks", json={"primaryAssetId": primary_asset_id, "assetIds": asset_ids})

    def get_stack(self, stack_id):
        """
        Get details of a specific asset stack.

        Args:
            stack_id (str): The UUID of the stack.

        Returns:
            dict: Stack metadata.
        """
        return self.get(f"stacks/{stack_id}")

    def update_stack(self, stack_id, primary_asset_id):
        """
        Update the primary asset of an existing stack.

        Args:
            stack_id (str): The UUID of the stack to update.
            primary_asset_id (str): The new primary asset UUID.

        Returns:
            dict: The updated stack metadata.
        """
        return self.put(f"stacks/{stack_id}", json={"primaryAssetId": primary_asset_id})

    def delete_stack(self, stack_id):
        """
        Delete a stack, releasing all assets (they are NOT deleted from the library).

        Args:
            stack_id (str): The UUID of the stack to delete.

        Returns:
            bool: True if deletion was successful (204 No Content).
        """
        return self.delete(f"stacks/{stack_id}")

    def remove_asset_from_stack(self, stack_id, asset_id):
        """
        Remove a specific asset from a stack.

        Args:
            stack_id (str): The UUID of the stack.
            asset_id (str): The UUID of the asset to remove from the stack.

        Returns:
            bool: True if removal was successful (204 No Content).
        """
        return self.delete(f"stacks/{stack_id}/assets/{asset_id}")
