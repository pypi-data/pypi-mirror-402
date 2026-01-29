from ..base import ImmichBaseClient

class TrashMixin(ImmichBaseClient):
    """
    Mixin for Trash related endpoints, handling soft-deleted items.
    """
    def get_trash(self):
        """
        Get all items currently in the trash.

        Returns:
            list: List of trashed asset metadata.
        """
        return self.get("trash")

    def empty_trash(self):
        """
        Permanently delete all items currently in the trash.

        Returns:
            bool: True if trash was successfully emptied (204 No Content).
        """
        return self.delete("trash")

    def restore_trash(self):
        """
        Restore all items from the trash back to the library.

        Returns:
            bool: True if restore was successfully triggered (204 No Content).
        """
        return self.post("trash/restore")

    def restore_assets(self, ids):
        """
        Restore specific assets from the trash.

        Args:
            ids (list): List of asset UUIDs to restore.

        Returns:
            bool: True if restoration was successful (200 OK).
        """
        return self.post("trash/restore/assets", json={"ids": ids})
