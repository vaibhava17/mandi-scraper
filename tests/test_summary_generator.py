import unittest
from datetime import date
from src.analytics.summary_generator import generate_daily_summary


class TestSummaryGenerator(unittest.TestCase):
    def test_generate_daily_summary_empty(self):
        """Test summary generation with empty input lists."""
        result = generate_daily_summary([], [], [])

        self.assertIn("date", result)
        self.assertEqual(result["date"], date.today().isoformat())
        self.assertEqual(result["total_mandi_records"], 0)
        self.assertEqual(result["total_plant_records"], 0)
        self.assertEqual(result["total_seed_records"], 0)
        self.assertEqual(result["mandi_highlights"], {})
        self.assertIn("Mandi Market Daily Brief", result["text_summary"])
        self.assertIn("0 Mandis | 0 Plant Rates | 0 Seeds", result["text_summary"])

    def test_generate_daily_summary_with_records(self):
        """Test summary aggregation calculations with sample mandi, plant, and seed records."""
        mandi_records = [
            {
                "commodity": "Tomato",
                "market": "Kolar",
                "state": "Karnataka",
                "price_per_kg": 25.0,
                "modal_price": 2500,
            },
            {
                "commodity": "Tomato",
                "market": "Nashik",
                "state": "Maharashtra",
                "price_per_kg": 35.0,
                "modal_price": 3500,
            },
            {
                "commodity": "Onion",
                "market": "Lasalgaon",
                "state": "Maharashtra",
                "price_per_kg": 20.0,
                "modal_price": 2000,
            },
        ]

        plant_records = [
            {
                "name": "Hybrid Tomato Sapling",
                "category": "Commercial Seedling",
                "variety": "Syngenta Saaho",
                "price_min": 1.10,
                "price_max": 1.50,
                "price": 1.30,
            },
            {
                "name": "Bonsai Ficus",
                "category": "Ornamental",
                "variety": "Ficus Retusa",
                "price_min": 250,
                "price_max": 400,
                "price": 300,
            },
        ]

        seed_records = [
            {
                "crop": "Tomato",
                "title": "Syngenta Saaho Seeds",
                "brand": "Syngenta",
                "pack_size": "3000 seeds",
                "price": 800.0,
            },
            {
                "crop": "Chilli",
                "title": "VNR 332 Chilli Seeds",
                "brand": "VNR",
                "pack_size": "10g",
                "price": 500.0,
            },
        ]

        result = generate_daily_summary(mandi_records, plant_records, seed_records)

        self.assertEqual(result["total_mandi_records"], 3)
        self.assertEqual(result["total_plant_records"], 2)
        self.assertEqual(result["total_seed_records"], 2)

        highlights = result["mandi_highlights"]
        self.assertIn("Tomato", highlights)
        self.assertEqual(highlights["Tomato"]["avg_kg"], 30.0)
        self.assertEqual(highlights["Tomato"]["min_kg"], 25.0)
        self.assertEqual(highlights["Tomato"]["max_kg"], 35.0)
        self.assertEqual(highlights["Tomato"]["sample_count"], 2)

        self.assertIn("Onion", highlights)
        self.assertEqual(highlights["Onion"]["avg_kg"], 20.0)
        self.assertEqual(highlights["Onion"]["min_kg"], 20.0)
        self.assertEqual(highlights["Onion"]["max_kg"], 20.0)
        self.assertEqual(highlights["Onion"]["sample_count"], 1)

        summary = result["text_summary"]
        self.assertIn("Nashik (Maharashtra) at ₹35.0/kg", summary)
        self.assertIn("Hybrid Tomato Sapling", summary)
        self.assertIn("Syngenta Saaho Seeds", summary)

    def test_generate_daily_summary_filtering_zero_prices(self):
        """Test that zero or negative price_per_kg records are excluded from averages."""
        mandi_records = [
            {
                "commodity": "Tomato",
                "market": "InvalidMarket",
                "state": "Test",
                "price_per_kg": 0.0,
                "modal_price": 0,
            },
            {
                "commodity": "Tomato",
                "market": "ValidMarket",
                "state": "Test",
                "price_per_kg": 40.0,
                "modal_price": 4000,
            },
        ]

        result = generate_daily_summary(mandi_records, [], [])
        highlights = result["mandi_highlights"]

        self.assertEqual(highlights["Tomato"]["avg_kg"], 40.0)
        self.assertEqual(highlights["Tomato"]["sample_count"], 1)


if __name__ == "__main__":
    unittest.main()
