import unittest
from unittest.mock import patch, MagicMock
import requests
import io
import sys
from immich_lib.base import ImmichBaseClient

class TestImmichBaseClient(unittest.TestCase):
    def setUp(self):
        self.server_url = "http://localhost:2283"
        self.api_key = "test-api-key"
        self.client = ImmichBaseClient(self.server_url, self.api_key)

    def test_init(self):
        self.assertEqual(self.client.server_url, "http://localhost:2283")
        self.assertEqual(self.client.api_url, "http://localhost:2283/api")
        self.assertEqual(self.client.headers["x-api-key"], self.api_key)
        self.assertEqual(self.client.session.headers["x-api-key"], self.api_key)

    @patch('requests.Session.request')
    def test_request_success_json(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json.return_value = {"status": "ok"}
        mock_request.return_value = mock_response

        result = self.client._request("GET", "test")
        self.assertEqual(result, {"status": "ok"})
        mock_request.assert_called()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertEqual(args[1], "http://localhost:2283/api/test")

    @patch('requests.Session.request')
    def test_request_success_204(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response

        result = self.client._request("DELETE", "test")
        self.assertTrue(result)

    @patch('requests.Session.request')
    def test_request_success_stream(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "image/jpeg"}
        mock_request.return_value = mock_response

        # Case 1: Stream requested
        result = self.client._request("GET", "test", stream=True)
        self.assertEqual(result, mock_response)

        # Case 2: Non-JSON content type
        result = self.client._request("GET", "test")
        self.assertEqual(result, mock_response)

    @patch('requests.Session.request')
    def test_request_error_with_json(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Bad Request"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Error", response=mock_response)
        mock_request.return_value = mock_response

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(requests.exceptions.HTTPError):
                self.client._request("GET", "test")
            self.assertIn("Immich API Error (400): Bad Request", fake_out.getvalue())

    @patch('requests.Session.request')
    def test_request_error_without_json(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception("No JSON")
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Internal Server Error", response=mock_response)
        mock_request.return_value = mock_response

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(requests.exceptions.HTTPError):
                self.client._request("GET", "test")
            self.assertIn("Immich API Error (500): Internal Server Error", fake_out.getvalue())

    @patch.object(ImmichBaseClient, '_request')
    def test_http_methods(self, mock_req):
        self.client.get("test", params={"q": 1})
        mock_req.assert_called_with("GET", "test", params={"q": 1})

        self.client.post("test", json={"a": 1})
        mock_req.assert_called_with("POST", "test", json={"a": 1})

        self.client.put("test", json={"a": 2})
        mock_req.assert_called_with("PUT", "test", json={"a": 2})

        self.client.delete("test")
        mock_req.assert_called_with("DELETE", "test")

        self.client.patch("test", json={"a": 3})
        mock_req.assert_called_with("PATCH", "test", json={"a": 3})

if __name__ == "__main__":
    unittest.main()
