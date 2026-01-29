from ..base import ImmichBaseClient

class ActivitiesMixin(ImmichBaseClient):
    """
    Mixin for Activities related endpoints.
    """
    def get_activities(self, album_id, asset_id=None, level=None, type=None, user_id=None):
        """List all activities"""
        params = {"albumId": album_id}
        if asset_id: params["assetId"] = asset_id
        if level: params["level"] = level
        if type: params["type"] = type
        if user_id: params["userId"] = user_id
        return self.get("activities", params=params)

    def create_activity(self, album_id, asset_id=None, comment=None, type="comment"):
        """Create an activity (like or comment)"""
        data = {
            "albumId": album_id,
            "type": type
        }
        if asset_id: data["assetId"] = asset_id
        if comment: data["comment"] = comment
        return self.post("activities", json=data)

    def delete_activity(self, activity_id):
        """Delete an activity"""
        return self.delete(f"activities/{activity_id}")

    def get_activity_statistics(self, album_id, asset_id=None):
        """Get activity statistics (likes/comments count)"""
        params = {"albumId": album_id}
        if asset_id: params["assetId"] = asset_id
        return self.get("activities/statistics", params=params)
