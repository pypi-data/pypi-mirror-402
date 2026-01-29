import unittest
from unittest.mock import patch, MagicMock
from immich_lib.client import ImmichClient

class TestApiMixins(unittest.TestCase):
    def setUp(self):
        self.client = ImmichClient("http://localhost:2283", "test-key")

    @patch.object(ImmichClient, 'get')
    def test_activities_mixin(self, mock_get):
        # get_activities
        self.client.get_activities("alb1", asset_id="ast1", level="info", type="comment", user_id="u1")
        mock_get.assert_called_with("activities", params={"albumId": "alb1", "assetId": "ast1", "level": "info", "type": "comment", "userId": "u1"})
        
        # get_activity_statistics
        self.client.get_activity_statistics("alb1", asset_id="ast1")
        mock_get.assert_called_with("activities/statistics", params={"albumId": "alb1", "assetId": "ast1"})

    @patch.object(ImmichClient, 'post')
    @patch.object(ImmichClient, 'delete')
    def test_activities_write(self, mock_delete, mock_post):
        # create_activity
        self.client.create_activity("alb1", asset_id="ast1", comment="nice", type="comment")
        mock_post.assert_called_with("activities", json={"albumId": "alb1", "type": "comment", "assetId": "ast1", "comment": "nice"})
        
        # delete_activity
        self.client.delete_activity("act1")
        mock_delete.assert_called_with("activities/act1")

    @patch.object(ImmichClient, 'get')
    def test_albums_mixin(self, mock_get):
        # We need to simulate the return value for internal calls in list_albums if shared is None
        mock_get.return_value = []
        self.client.list_albums(shared=True)
        mock_get.assert_called_with("albums", params={"shared": "true"})
        
        self.client.get_album("alb1")
        mock_get.assert_called_with("albums/alb1")

    @patch.object(ImmichClient, 'post')
    @patch.object(ImmichClient, 'delete')
    @patch.object(ImmichClient, 'patch')
    def test_albums_write(self, mock_patch, mock_delete, mock_post):
        self.client.create_album("New Album", description="desc")
        mock_post.assert_called_with("albums", json={"albumName": "New Album", "description": "desc"})
        
        self.client.update_album("alb1", album_name="Updated")
        mock_patch.assert_called_with("albums/alb1", json={"albumName": "Updated"})
        
        self.client.delete_album("alb1")
        mock_delete.assert_called_with("albums/alb1")

    @patch.object(ImmichClient, 'get')
    @patch.object(ImmichClient, 'post')
    @patch.object(ImmichClient, 'delete')
    @patch.object(ImmichClient, 'put')
    def test_assets_mixin(self, mock_put, mock_delete, mock_post, mock_get):
        # get_asset_info
        self.client.get_asset_info("ast1")
        mock_get.assert_called_with("assets/ast1")
        
        # update_asset
        self.client.update_asset("ast1", isFavorite=True)
        mock_put.assert_called_with("assets/ast1", json={"isFavorite": True})
        
        # delete_assets
        self.client.delete_assets(["ast1"])
        mock_delete.assert_called_with("assets", json={"ids": ["ast1"]})

        # list_assets calls search/metadata
        mock_post.return_value = {"assets": {"items": []}}
        self.client.list_assets(isFavorite=True)
        mock_post.assert_called_with("search/metadata", json={"isFavorite": True})

    @patch.object(ImmichClient, 'post')
    @patch.object(ImmichClient, 'get')
    def test_search_mixin(self, mock_get, mock_post):
        # search_metadata
        self.client.search_metadata(query="test")
        mock_post.assert_called_with("search/metadata", json={"query": "test"})
        
        # search_places
        self.client.search_places(query="Berlin")
        mock_get.assert_called_with("search/places", params={"query": "Berlin"})

    @patch.object(ImmichClient, 'get')
    def test_users_mixin(self, mock_get):
        self.client.get_me()
        mock_get.assert_called_with("users/me")
        
        self.client.list_users()
        mock_get.assert_called_with("users")

    @patch.object(ImmichClient, 'get')
    def test_system_mixin(self, mock_get):
        self.client.get_server_info()
        mock_get.assert_called_with("server/info")
        
        self.client.get_storage_info()
        mock_get.assert_called_with("system-metadata/storage-info")

    @patch.object(ImmichClient, 'get')
    @patch.object(ImmichClient, 'post')
    def test_people_mixin(self, mock_post, mock_get):
        self.client.get_all_people()
        mock_get.assert_called_with("people", params={'withHidden': False})
        
        self.client.merge_people("p1", ["p2", "p3"])
        mock_post.assert_called_with("people/p1/merge", json={"ids": ["p2", "p3"]})

    @patch.object(ImmichClient, 'get')
    def test_folders_mixin(self, mock_get):
        self.client.list_folders()
        mock_get.assert_called_with("folders")

    @patch.object(ImmichClient, 'get')
    @patch.object(ImmichClient, 'put')
    def test_jobs_mixin(self, mock_put, mock_get):
        self.client.list_jobs()
        mock_get.assert_called_with("jobs")
        
        self.client.run_job("j1", "start")
        mock_put.assert_called_with("jobs/j1", json={"command": "start", "force": False})

    @patch.object(ImmichClient, 'get')
    @patch.object(ImmichClient, 'put')
    def test_tags_mixin(self, mock_put, mock_get):
        self.client.list_tags()
        mock_get.assert_called_with("tags")
        
        self.client.tag_assets("t1", ["a1"])
        mock_put.assert_called_with("tags/t1/assets", json={"ids": ["a1"]})

    @patch.object(ImmichClient, 'get')
    def test_trash_mixin(self, mock_get):
        self.client.get_trash()
        mock_get.assert_called_with("trash")

    @patch.object(ImmichClient, 'get')
    def test_partners_mixin(self, mock_get):
        self.client.list_partners()
        mock_get.assert_called_with("partners", params={"direction": "shared-with-me"})

    @patch.object(ImmichClient, 'get')
    def test_stacks_mixin(self, mock_get):
        self.client.get_stack("stack1")
        mock_get.assert_called_with("stacks/stack1")

    @patch.object(ImmichClient, 'get')
    def test_misc_mixin(self, mock_get):
        self.client.get_library_info()
        mock_get.assert_called_with("library")

if __name__ == "__main__":
    unittest.main()
