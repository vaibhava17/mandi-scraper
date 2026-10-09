import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from src.scrapers.mandi_scraper import MandiScraper


class TestMandiScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = MandiScraper(datagov_api_key="test_key_123")

    def test_init_defaults(self):
        scraper = MandiScraper()
        self.assertIn("mandi-scraper/1.0", scraper.session.headers["User-Agent"])
        self.assertEqual(scraper.session.headers["Accept"], "application/json")

    def test_normalize_mirror_records(self):
        raw_records = [
            {
                "state": "Maharashtra",
                "district": "Nashik",
                "market": "Lasalgaon",
                "commodity": "Onion",
                "variety": "Red",
                "grade": "FAQ",
                "min_price": "1500",
                "max_price": "2200",
                "modal_price": "1800",
                "arrival_date": "2026-10-09",
            },
            {
                "state": "Karnataka",
                "district": "Kolar",
                "market": "Kolar",
                "commodity": "Tomato",
                "min_price": "2000",
                "max_price": "3000",
                "modal_price": "2500",
            },
        ]

        normalized = self.scraper._normalize_mirror_records(raw_records)
        self.assertEqual(len(normalized), 2)

        r1 = normalized[0]
        self.assertEqual(r1["state"], "Maharashtra")
        self.assertEqual(r1["commodity"], "Onion")
        self.assertEqual(r1["modal_price"], 1800.0)
        self.assertEqual(r1["price_per_kg"], 18.0)
        self.assertEqual(r1["arrival_date"], "2026-10-09")
        self.assertEqual(r1["source"], "agmarknet_mirror")

        r2 = normalized[1]
        self.assertEqual(r2["variety"], "Local")
        self.assertEqual(r2["grade"], "FAQ")
        self.assertEqual(r2["price_per_kg"], 25.0)
        self.assertEqual(r2["arrival_date"], date.today().isoformat())

    def test_normalize_ogd_records(self):
        raw_records = [
            {
                "State": "Punjab",
                "District": "Ludhiana",
                "Market": "Ludhiana",
                "Commodity": "Potato",
                "Variety": "Jyoti",
                "Grade": "Super",
                "Min Price": "1200",
                "Max Price": "1600",
                "Modal Price": "1400",
                "Arrival_Date": "2026-10-08",
            }
        ]

        normalized = self.scraper._normalize_ogd_records(raw_records)
        self.assertEqual(len(normalized), 1)

        r = normalized[0]
        self.assertEqual(r["state"], "Punjab")
        self.assertEqual(r["district"], "Ludhiana")
        self.assertEqual(r["commodity"], "Potato")
        self.assertEqual(r["variety"], "Jyoti")
        self.assertEqual(r["grade"], "Super")
        self.assertEqual(r["modal_price"], 1400.0)
        self.assertEqual(r["price_per_kg"], 14.0)
        self.assertEqual(r["arrival_date"], "2026-10-08")
        self.assertEqual(r["source"], "data.gov.in")

    def test_normalize_records_graceful_skipping(self):
        """Test that malformed records don't raise uncaught exceptions."""
        raw_mirror = [{"state": "Bad", "min_price": "not_a_number"}]
        # float("not_a_number") raises ValueError, handled gracefully in loop
        normalized = self.scraper._normalize_mirror_records(raw_mirror)
        self.assertEqual(len(normalized), 0)

    @patch("src.scrapers.mandi_scraper.requests.Session.get")
    def test_fetch_from_public_mirror_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [
                {
                    "state": "Gujarat",
                    "market": "Surat",
                    "commodity": "Cabbage",
                    "modal_price": 1000,
                }
            ]
        }
        mock_get.return_value = mock_resp

        res = self.scraper.fetch_from_public_mirror(commodity="Cabbage")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["commodity"], "Cabbage")
        self.assertEqual(res[0]["price_per_kg"], 10.0)

    @patch("src.scrapers.mandi_scraper.requests.Session.get")
    def test_fetch_from_public_mirror_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        res = self.scraper.fetch_from_public_mirror(commodity="Tomato")
        self.assertEqual(res, [])

    def test_fetch_from_ogd_without_key(self):
        scraper_no_key = MandiScraper(datagov_api_key=None)
        res = scraper_no_key.fetch_from_ogd(commodity="Tomato")
        self.assertEqual(res, [])

    @patch("src.scrapers.mandi_scraper.requests.Session.get")
    def test_fetch_from_ogd_with_key_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [
                {
                    "State": "Haryana",
                    "Market": "Karnal",
                    "Commodity": "Tomato",
                    "Modal Price": 3000,
                }
            ]
        }
        mock_get.return_value = mock_resp

        res = self.scraper.fetch_from_ogd(commodity="Tomato")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["commodity"], "Tomato")
        self.assertEqual(res[0]["price_per_kg"], 30.0)

    @patch.object(MandiScraper, "fetch_from_ogd")
    @patch.object(MandiScraper, "fetch_from_public_mirror")
    def test_scrape_all_fallback(self, mock_mirror, mock_ogd):
        mock_ogd.return_value = []
        mock_mirror.return_value = [{"commodity": "Tomato", "price_per_kg": 20.0}]

        results = self.scraper.scrape_all(commodities=["Tomato"])
        self.assertEqual(len(results), 1)
        mock_ogd.assert_called_once_with(commodity="Tomato", limit=200)
        mock_mirror.assert_called_once_with(commodity="Tomato", limit=200)


if __name__ == "__main__":
    unittest.main()
