from ..base import ImmichBaseClient

class FoldersMixin(ImmichBaseClient):
    """
    Mixin for Folders related endpoints.
    """
    def list_folders(self):
        """Get all external folders"""
        return self.get("folders")

    def create_folder(self, import_path):
        """Add an external folder"""
        return self.post("folders", json={"importPath": import_path})

    def delete_folder(self, folder_id):
        """Remove an external folder"""
        return self.delete(f"folders/{folder_id}")
