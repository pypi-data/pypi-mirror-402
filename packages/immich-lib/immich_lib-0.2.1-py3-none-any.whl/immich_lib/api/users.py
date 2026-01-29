from ..base import ImmichBaseClient

class UsersMixin(ImmichBaseClient):
    """
    Mixin for Users related endpoints, handling user management and profile retrieval.
    """
    def list_users(self):
        """
        Retrieve a list of all users on the server.

        Returns:
            list: A list of user data dictionaries.
        """
        return self.get("users")

    def create_user(self, email, password, name, is_admin=False):
        """
        Create a new user on the server.

        Args:
            email (str): The email address for the new user.
            password (str): The password for the new user.
            name (str): The display name for the new user.
            is_admin (bool): Whether to grant admin privileges.

        Returns:
            dict: The created user metadata.
        """
        data = {
            "email": email,
            "password": password,
            "name": name,
            "isAdmin": is_admin
        }
        return self.post("users", json=data)

    def get_me(self):
        """
        Get information about the current authenticated user.

        Returns:
            dict: The current user's metadata.
        """
        return self.get("users/me")

    def get_user(self, user_id):
        """
        Get information about a specific user.

        Args:
            user_id (str): The UUID of the user.

        Returns:
            dict: User metadata.
        """
        return self.get(f"users/{user_id}")

    def update_user(self, user_id, **kwargs):
        """
        Update user information.

        Args:
            user_id (str): The UUID of the user to update.
            **kwargs: Fields to update (email, name, password, isAdmin, etc.).

        Returns:
            dict: The updated user metadata.
        """
        return self.put(f"users/{user_id}", json=kwargs)

    def delete_user(self, user_id):
        """
        Delete a user.

        Args:
            user_id (str): The UUID of the user to delete.

        Returns:
            bool: True if deletion was successful (204 No Content).
        """
        return self.delete(f"users/{user_id}")
