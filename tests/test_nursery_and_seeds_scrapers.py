import unittest
from unittest.mock import patch
from src.scrapers.nursery_plants_scraper import (
    NurseryPlantsScraper,
    COMMERCIAL_VEGETABLE_SAPLINGS_INDEX,
)
from src.scrapers.seed_prices_scraper import (
    SeedPricesScraper,
    COMMERCIAL_HYBRID_SEEDS_BENCHMARKS,
)


class TestNurseryAndSeedsScrapers(unittest.TestCase):
    def test_commercial_saplings_index_integrity(self):
        """Verify commercial sapling benchmark index fields and pricing consistency."""
        self.assertGreater(len(COMMERCIAL_VEGETABLE_SAPLINGS_INDEX), 0)
        valid_categories = {"Commercial Seedling", "Fruit Sapling", "Floriculture Seedling"}
        for item in COMMERCIAL_VEGETABLE_SAPLINGS_INDEX:
            self.assertIn("name", item)
            self.assertIn("crop", item)
            self.assertIn("category", item)
            self.assertIn(item["category"], valid_categories)
            self.assertIn("price_min", item)
            self.assertIn("price_max", item)
            self.assertIn("price", item)
            self.assertGreater(item["price_min"], 0)
            self.assertGreaterEqual(item["price_max"], item["price_min"])
            self.assertTrue(item["price_min"] <= item["price"] <= item["price_max"])

    def test_nursery_plants_scraper_scrape_all(self):
        """Verify NurseryPlantsScraper returns baseline benchmarks even if web requests fail."""
        scraper = NurseryPlantsScraper()
        # Mocking external store scrapers to avoid hitting live web endpoints during tests
        with patch.object(scraper, "scrape_plantsguru", return_value=[]), \
             patch.object(scraper, "scrape_trustbasket_plants", return_value=[]):
            results = scraper.scrape_all()
            self.assertGreaterEqual(len(results), len(COMMERCIAL_VEGETABLE_SAPLINGS_INDEX))
            for r in results:
                self.assertIn("name", r)
                self.assertIn("category", r)
                self.assertIn("scraped_date", r)

    def test_commercial_seeds_benchmarks_integrity(self):
        """Verify commercial hybrid seed benchmark fields and pricing consistency."""
        self.assertGreater(len(COMMERCIAL_HYBRID_SEEDS_BENCHMARKS), 0)
        for item in COMMERCIAL_HYBRID_SEEDS_BENCHMARKS:
            self.assertIn("title", item)
            self.assertIn("crop", item)
            self.assertIn("price", item)
            self.assertIn("mrp", item)
            self.assertGreater(item["price"], 0)
            self.assertGreaterEqual(item["mrp"], item["price"])

    def test_seed_prices_scraper_scrape_all(self):
        """Verify SeedPricesScraper returns benchmark catalog records."""
        scraper = SeedPricesScraper()
        with patch.object(scraper, "scrape_agribegri_seeds", return_value=[]), \
             patch.object(scraper, "scrape_trustbasket_seeds", return_value=[]):
            results = scraper.scrape_all()
            self.assertGreaterEqual(len(results), len(COMMERCIAL_HYBRID_SEEDS_BENCHMARKS))
            for r in results:
                self.assertIn("title", r)
                self.assertIn("crop", r)
                self.assertIn("price", r)
                self.assertIn("scraped_date", r)


if __name__ == "__main__":
    unittest.main()
