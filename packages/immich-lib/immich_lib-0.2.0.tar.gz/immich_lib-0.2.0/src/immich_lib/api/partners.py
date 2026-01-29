from ..base import ImmichBaseClient

class PartnersMixin(ImmichBaseClient):
    """
    Mixin for Partner sharing related endpoints, allowing shared library access between users.
    """
    def list_partners(self, direction="shared-with-me"):
        """
        Get partners the user is sharing with or who are sharing with the user.

        Args:
            direction (str): 'shared-with-me' to see who shares with you, 
                             'shared-by-me' to see who you share with.

        Returns:
            list: List of partner metadata.
        """
        return self.get("partners", params={"direction": direction})

    def create_partner(self, partner_id):
        """
        Start sharing your library with another user as a partner.

        Args:
            partner_id (str): The UUID of the user to become your partner.

        Returns:
            dict: The created partner relationship metadata.
        """
        return self.post(f"partners/{partner_id}")

    def update_partner(self, partner_id, **kwargs):
        """
        Update the sharing settings for a specific partner.

        Args:
            partner_id (str): The UUID of the partner.
            **kwargs: Sharing settings (e.g., isArchived, isFavorite).

        Returns:
            dict: The updated partner relationship metadata.
        """
        return self.put(f"partners/{partner_id}", json=kwargs)

    def delete_partner(self, partner_id):
        """
        Stop sharing your library with a partner or remove a shared partner library.

        Args:
            partner_id (str): The UUID of the partner user.

        Returns:
            bool: True if partner relationship was successfully removed (204 No Content).
        """
        return self.delete(f"partners/{partner_id}")
