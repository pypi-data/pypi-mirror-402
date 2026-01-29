from ..base import ImmichBaseClient

class PeopleMixin(ImmichBaseClient):
    """
    Mixin for People related endpoints, handling facial recognition results and person metadata.
    """
    def get_all_people(self, with_hidden=False):
        """
        Retrieve a list of all detected people who are not hidden.

        Args:
            with_hidden (bool): Whether to include people marked as hidden.

        Returns:
            dict: Response containing the list of people.
        """
        return self.get("people", params={"withHidden": with_hidden})

    def get_person(self, person_id):
        """
        Get information about a specific person by their UUID.

        Args:
            person_id (str): The UUID of the person.

        Returns:
            dict: Person metadata (name, thumbnail, etc.).
        """
        return self.get(f"people/{person_id}")

    def update_person(self, person_id, **kwargs):
        """
        Update a person's information (e.g., set their name).

        Args:
            person_id (str): The UUID of the person.
            **kwargs: Fields to update (e.g., 'name', 'birthDate', 'isHidden').

        Returns:
            dict: The updated person metadata.
        """
        return self.put(f"people/{person_id}", json=kwargs)

    def get_person_assets(self, person_id):
        """
        Get all assets associated with a specific person.

        Args:
            person_id (str): The UUID of the person.

        Returns:
            list: List of asset metadata for that person.
        """
        return self.get(f"people/{person_id}/assets")

    def merge_people(self, primary_person_id, subordinate_person_ids):
        """
        Merge multiple detected people into a single person entry.

        Args:
            primary_person_id (str): The UUID of the person to keep.
            subordinate_person_ids (list): List of UUIDs for people to merge into the primary entry.

        Returns:
            list: List of UUIDs that were successfully merged.
        """
        data = {"ids": subordinate_person_ids}
        return self.post(f"people/{primary_person_id}/merge", json=data)
