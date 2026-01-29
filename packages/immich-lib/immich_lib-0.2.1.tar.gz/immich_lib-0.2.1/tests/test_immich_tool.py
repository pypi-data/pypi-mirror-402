"""
Unit tests for the Immich CLI Tool.

These tests use the 'unittest' framework and 'unittest.mock' to verify the behavior
of the ImmichClient class and the CLI entry point without requiring a live server.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import io
import json
from immich_lib.client import ImmichClient
from immich_lib.cli import main

class TestImmichClient(unittest.TestCase):
    """Test suite for the ImmichClient class."""

    def setUp(self):
        """Set up a fresh ImmichClient instance before each test."""
        self.client = ImmichClient("http://fake-server", "fake-key")

    @patch('requests.Session.request')
    def test_check_auth_success(self, mock_request):
        """Test success case where version and albums endpoints both return 200."""
        mock_version = MagicMock()
        mock_version.status_code = 200
        mock_version.headers = {"Content-Type": "application/json"}
        mock_version.json.return_value = {"version": "1.0.0"}
        
        mock_albums = MagicMock()
        mock_albums.status_code = 200
        mock_albums.headers = {"Content-Type": "application/json"}
        
        mock_request.side_effect = [mock_version, mock_albums]

        result = self.client.check_auth()
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(mock_request.call_count, 2)

    @patch('requests.Session.request')
    def test_check_auth_failure_version(self, mock_request):
        """Test failure when the version endpoint fails."""
        mock_request.side_effect = Exception("Network Error")
        with patch('sys.stdout', new=io.StringIO()):
            result = self.client.check_auth()
        self.assertIsNone(result)

    @patch('requests.Session.request')
    def test_list_albums_success(self, mock_request):
        """Test merging of owned and shared albums."""
        # Owned albums
        m1 = MagicMock()
        m1.status_code = 200
        m1.headers = {"Content-Type": "application/json"}
        m1.json.return_value = [{"id": "a1", "albumName": "Owned"}]
        
        # Shared albums (with one overlap to test deduplication)
        m2 = MagicMock()
        m2.status_code = 200
        m2.headers = {"Content-Type": "application/json"}
        m2.json.return_value = [
            {"id": "a1", "albumName": "Owned (but also shared)"},
            {"id": "a2", "albumName": "Shared"}
        ]
        
        mock_request.side_effect = [m1, m2]

        result = self.client.list_albums()
        self.assertEqual(len(result), 2)
        ids = [a['id'] for a in result]
        self.assertIn("a1", ids)
        self.assertIn("a2", ids)

    @patch('requests.Session.request')
    def test_get_album_success(self, mock_request):
        """Test retrieving specific album details."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"id": "a1", "assets": [{"id": "p1"}]}
        mock_request.return_value = mock_response

        result = self.client.get_album("a1")
        self.assertEqual(result["id"], "a1")
        self.assertEqual(len(result["assets"]), 1)

    @patch('requests.Session.request')
    def test_list_assets_success(self, mock_request):
        """Test discovery of assets via search endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {
            "assets": {"items": [{"id": "p1", "type": "IMAGE"}]}
        }
        mock_request.return_value = mock_response

        result = self.client.list_assets()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "p1")

    def test_find_album_by_id(self):
        """Test find_album method with a UUID."""
        with patch.object(self.client, 'list_albums', return_value=[{"id": "a1", "albumName": "Test"}]):
            result = self.client.find_album("a1")
            self.assertEqual(result["albumName"], "Test")

    def test_find_album_by_name(self):
        """Test find_album method with a name match."""
        with patch.object(self.client, 'list_albums', return_value=[{"id": "a1", "albumName": "Vacation"}]):
            result = self.client.find_album("vacation") # Case insensitive
            self.assertEqual(result["id"], "a1")

    @patch('requests.Session.request')
    def test_get_asset_info_success(self, mock_request):
        """Test retrieving asset metadata."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"id": "p1", "originalFileName": "file.jpg"}
        mock_request.return_value = mock_response

        result = self.client.get_asset_info("p1")
        self.assertEqual(result["originalFileName"], "file.jpg")

    @patch('builtins.open', new_callable=mock_open)
    @patch('requests.Session.request')
    def test_download_asset_success(self, mock_request, mock_file):
        """Test downloading an asset with streaming."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '10'}
        mock_response.iter_content.return_value = [b'0123456789']
        mock_request.return_value = mock_response

        with patch('immich_lib.api.assets.tqdm'):
            result = self.client.download_asset("p1", "local.jpg")

        self.assertTrue(result)
        mock_file().write.assert_called_with(b'0123456789')

class TestMain(unittest.TestCase):
    """Test suite for the main CLI entry point."""

    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch('sys.exit')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_missing_config(self, mock_stdout, mock_exit):
        """Test that script exits if URL/Key are missing."""
        mock_exit.side_effect = SystemExit(1)
        with patch('immich_lib.cli.IMMICH_SERVER_URL', None):
            with patch('immich_lib.cli.IMMICH_API_KEY', None):
                with patch('sys.argv', ['immich-tool', 'list-albums']):
                    with self.assertRaises(SystemExit):
                        main()
        self.assertIn("Error: Immich URL and API Key must be provided", mock_stdout.getvalue())

    @patch('immich_lib.cli.ImmichClient')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_list_assets(self, mock_stdout, MockClient):
        """Test CLI output for 'list-assets'."""
        mock_instance = MockClient.return_value
        mock_instance.list_assets.return_value = [{'id': 'p1', 'originalFileName': 'test.jpg', 'type': 'IMAGE'}]
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'list-assets']):
            main()
        
        output = mock_stdout.getvalue()
        self.assertIn("p1", output)
        self.assertIn("test.jpg", output)

    @patch('immich_lib.cli.ImmichClient')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_list_album_assets(self, mock_stdout, MockClient):
        """Test CLI output for 'list-album-assets'."""
        # Use simple return values for nested calls
        mock_instance = MockClient.return_value
        mock_instance.find_album.return_value = {'id': 'a1', 'albumName': 'MyAlbum'}
        mock_instance.get_album.return_value = {
            'id': 'a1', 'assets': [{'id': 'p1', 'originalFileName': 'img.jpg', 'type': 'IMAGE'}]
        }
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'list-album-assets', 'MyAlbum']):
            main()
        
        output = mock_stdout.getvalue()
        self.assertIn("img.jpg", output)

    @patch('immich_lib.cli.ImmichClient')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_check_auth_failure(self, mock_stdout, MockClient):
        """Test CLI output when authentication fails."""
        mock_instance = MockClient.return_value
        mock_instance.check_auth.return_value = None
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'check-auth']):
            main()
        
        self.assertIn("Authentication failed", mock_stdout.getvalue())

    @patch('immich_lib.cli.ImmichClient')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_list_albums_empty(self, mock_stdout, MockClient):
        """Test CLI output when no albums are found."""
        mock_instance = MockClient.return_value
        mock_instance.list_albums.return_value = []
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'list-albums']):
            main()
        
        self.assertIn("No albums found", mock_stdout.getvalue())

    @patch('immich_lib.cli.ImmichClient')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_list_albums(self, mock_stdout, MockClient):
        """Test CLI output for 'list-albums'."""
        mock_instance = MockClient.return_value
        mock_instance.list_albums.return_value = [{'id': 'a1', 'albumName': 'Test', 'assetCount': 2}]
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'list-albums']):
            main()
        
        self.assertIn("Test", mock_stdout.getvalue())

    @patch('immich_lib.cli.ImmichClient')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_get_metadata(self, mock_stdout, MockClient):
        """Test CLI output for 'get-metadata'."""
        mock_instance = MockClient.return_value
        mock_instance.get_asset_info.return_value = {'id': 'p1'}
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'get-metadata', 'p1']):
            main()
        
        self.assertIn('"id": "p1"', mock_stdout.getvalue())

    @patch('immich_lib.cli.ImmichClient')
    def test_main_download_album(self, MockClient):
        """Test 'download-album' command dispatch."""
        mock_instance = MockClient.return_value
        mock_instance.find_album.return_value = {'id': 'a1', 'albumName': 'Album'}
        mock_instance.get_album.return_value = {
            'id': 'a1', 'albumName': 'Album', 'assets': [{'id': 'p1', 'originalFileName': 'f.jpg'}]
        }
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'download-album', 'Album']):
            with patch('os.makedirs'):
                main()
        
        mock_instance.download_asset.assert_called()

    @patch('immich_lib.cli.ImmichClient')
    def test_main_download_asset(self, MockClient):
        """Test 'download-asset' command dispatch."""
        mock_instance = MockClient.return_value
        mock_instance.get_asset_info.return_value = {'originalFileName': 'f.jpg'}
        
        with patch('sys.argv', ['immich-tool', '--url', 'u', '--key', 'k', 'download-asset', 'p1']):
            main()
        
        mock_instance.download_asset.assert_called_with('p1', 'f.jpg')

if __name__ == "__main__":
    unittest.main()
