from ..base import ImmichBaseClient

class SystemMixin(ImmichBaseClient):
    """
    Mixin for System and Server related endpoints, providing server status and stats.
    """
    def get_server_version(self):
        """
        Get the current version of the Immich server.

        Returns:
            dict: Server version (major, minor, patch, etc.).
        """
        return self.get("server/version")

    def get_server_info(self):
        """
        Get general server information.

        Returns:
            dict: Server info metadata.
        """
        return self.get("server/info")

    def get_server_statistics(self):
        """
        Get statistical data about the server (assets, users, etc.).

        Returns:
            dict: Server statistics.
        """
        return self.get("server/statistics")

    def get_server_config(self):
        """
        Get the server's public configuration.

        Returns:
            dict: Server configuration.
        """
        return self.get("server/config")

    def get_storage_info(self):
        """
        Get storage usage details for the server.

        Returns:
            dict: Storage info (usage, available space).
        """
        return self.get("system-metadata/storage-info")

    def check_auth(self):
        """
        Verify the connection and authentication with the Immich server.

        Returns:
            dict | None: Server version info if successful, None if auth fails or unreachable.
        """
        try:
            version_info = self.get_server_version()
            # Verify API key by calling a simple protected endpoint
            self.get("albums")
            return version_info
        except Exception:
            return None
