import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app

# Set required environment variables for testing
os.environ["IMAGE_BRIDGE_API_KEY"] = "test_key"
os.environ["IMAGE_BRIDGE_OUTPUT_ROOT"] = "/tmp/image_bridge_test"

client = TestClient(app)

class TestBatchGeneration(unittest.TestCase):
    @patch("app.generate_image_bytes")
    @patch("app.write_bytes")
    def test_batch_generate_images_success(self, mock_write, mock_generate):
        try:
            # Setup mocks
            mock_generate.return_value = (b"fake_bytes", "image/png", 1024, 1024)
            
            payload = {
                "style_anchor": "luxury, cinematic",
                "items": [
                    {"prompt": "a red car", "out_path": "car1.png"},
                    {"prompt": "a blue car", "out_path": "car2.png"}
                ]
            }
            
            headers = {"X-API-Key": "test_key"}
            response = client.post("/generate-images", json=payload, headers=headers)
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["ok"])
            self.assertEqual(len(data["results"]), 2)
            
            # Verify prompt concatenation
            self.assertEqual(mock_generate.call_count, 2)
            mock_generate.assert_any_call("luxury, cinematic a red car")
            mock_generate.assert_any_call("luxury, cinematic a blue car")
        except Exception as e:
            print(f"\nFAILURE DETAILS: {e}")
            if 'response' in locals():
                print(f"RESPONSE STATUS: {response.status_code}")
                print(f"RESPONSE BODY: {response.text}")
            raise

    def test_batch_generate_unauthorized(self):
        payload = {"items": [{"prompt": "test", "out_path": "test.png"}]}
        response = client.post("/generate-images", json=payload)
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
