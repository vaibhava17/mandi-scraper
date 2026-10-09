import unittest
from unittest.mock import patch, MagicMock
from src.main import send_whatsapp_summary, main


class TestMain(unittest.TestCase):
    @patch("src.main.requests.post")
    def test_send_whatsapp_summary_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        send_whatsapp_summary("Test message")
        mock_post.assert_called_once()

    @patch("src.main.requests.post")
    def test_send_whatsapp_summary_handles_exception(self, mock_post):
        mock_post.side_effect = Exception("Connection error")
        # Should not raise exception
        send_whatsapp_summary("Test message")

    @patch("sys.argv", ["main.py", "--dry-run"])
    @patch("src.main.MandiScraper")
    @patch("src.main.NurseryPlantsScraper")
    @patch("src.main.SeedPricesScraper")
    @patch("src.main.get_database")
    def test_main_dry_run_does_not_call_db(
        self, mock_get_db, mock_seeds, mock_plants, mock_mandi
    ):
        mock_mandi.return_value.scrape_all.return_value = []
        mock_plants.return_value.scrape_all.return_value = []
        mock_seeds.return_value.scrape_all.return_value = []

        main()

        # Database should NOT be initialized on dry run
        mock_get_db.assert_not_called()


if __name__ == "__main__":
    unittest.main()
