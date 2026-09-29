"""
Nursery Plants & Saplings Rate List Scraper.
Collects wholesale commercial seedling benchmarks and live retail plant/sapling rates across India.
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date

logger = logging.getLogger("mandi_scraper.scrapers.plants")


# Verified Indian Commercial Nursery Baseline Index (Benchmark rates for pro-tray vegetable saplings)
# Sourced from major horticulture clusters: Karnal (Haryana), Malerkotla (Punjab),
# Kolar & Chikkaballapur (Karnataka), Nashik & Pune (Maharashtra), and Bareilly/Lucknow (UP).
COMMERCIAL_VEGETABLE_SAPLINGS_INDEX = [
    {
        "name": "Hybrid Tomato Sapling (25-30 Days)",
        "crop": "Tomato",
        "category": "Commercial Seedling",
        "variety": "Syngenta Saaho / US 440 / Abhinav",
        "plant_stage": "Pro-Tray Seedling (104-cavity)",
        "unit": "per sapling",
        "price_min": 0.85,
        "price_max": 1.60,
        "price": 1.20,
        "location": "Pan-India Nursery Hubs (Kolar/Nashik/Karnal)",
        "vendor": "Commercial Nursery Benchmark",
    },
    {
        "name": "Grafted Tomato Sapling (Bacterial Wilt Resistant)",
        "crop": "Tomato",
        "category": "Commercial Seedling",
        "variety": "Wild Brinjal / Solanum Torvum Rootstock",
        "plant_stage": "Hardened Grafted Sapling",
        "unit": "per sapling",
        "price_min": 4.50,
        "price_max": 7.50,
        "price": 6.00,
        "location": "South & Western India Nurseries",
        "vendor": "Commercial Nursery Benchmark",
    },
    {
        "name": "Hybrid Green Chilli Sapling",
        "crop": "Chilli",
        "category": "Commercial Seedling",
        "variety": "VNR 332 / Syngenta Sitara / Teja",
        "plant_stage": "Pro-Tray Seedling (104-cavity)",
        "unit": "per sapling",
        "price_min": 0.90,
        "price_max": 1.80,
        "price": 1.35,
        "location": "Andhra / Maharashtra / Karnataka Hubs",
        "vendor": "Commercial Nursery Benchmark",
    },
    {
        "name": "Hybrid Brinjal (Eggplant) Sapling",
        "crop": "Brinjal",
        "category": "Commercial Seedling",
        "variety": "VNR 212 / Mahyco Ravaiya",
        "plant_stage": "Pro-Tray Seedling (104-cavity)",
        "unit": "per sapling",
        "price_min": 0.80,
        "price_max": 1.50,
        "price": 1.15,
        "location": "UP / Haryana / Gujarat Nursery Hubs",
        "vendor": "Commercial Nursery Benchmark",
    },
    {
        "name": "Hybrid Capsicum / Shimla Mirch Sapling",
        "crop": "Capsicum",
        "category": "Commercial Seedling",
        "variety": "Syngenta Indra / Bachata (Color Capsicum)",
        "plant_stage": "Pro-Tray Seedling (104-cavity)",
        "unit": "per sapling",
        "price_min": 1.25,
        "price_max": 2.50,
        "price": 1.85,
        "location": "Polyhouse Nursery Clusters (Pune/Bangalore)",
        "vendor": "Commercial Nursery Benchmark",
    },
    {
        "name": "Papaya Grafted / Taiwan 786 Sapling",
        "crop": "Papaya",
        "category": "Fruit Sapling",
        "variety": "Red Lady 786",
        "plant_stage": "Polybags (45-60 Days Old)",
        "unit": "per sapling",
        "price_min": 25.00,
        "price_max": 45.00,
        "price": 35.00,
        "location": "Gujarat / Maharashtra / MP Nursery Hubs",
        "vendor": "Commercial Nursery Benchmark",
    },
    {
        "name": "Marigold (Genda) Flower Seedling",
        "crop": "Marigold",
        "category": "Floriculture Seedling",
        "variety": "Pusa Narangi / Calcutta Orange",
        "plant_stage": "Pro-Tray Seedling (126-cavity)",
        "unit": "per sapling",
        "price_min": 0.50,
        "price_max": 1.20,
        "price": 0.85,
        "location": "All India Seasonal Nurseries",
        "vendor": "Commercial Nursery Benchmark",
    },
]


class NurseryPlantsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })

    def scrape_commercial_benchmarks(self) -> List[Dict[str, Any]]:
        """Return structured commercial horticulture nursery benchmarks."""
        today_str = date.today().isoformat()
        records = []
        for item in COMMERCIAL_VEGETABLE_SAPLINGS_INDEX:
            records.append({
                **item,
                "scraped_date": today_str,
                "currency": "INR",
                "source": "reference_benchmark",
                "is_reference": True,
            })
        return records

    def scrape_plantsguru(self) -> List[Dict[str, Any]]:
        """Scrape live plant & sapling catalog from PlantsGuru."""
        records = []
        today_str = date.today().isoformat()
        url = "https://www.plantsguru.com/products.json?limit=250"

        try:
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                products = resp.json().get("products", [])
                for p in products:
                    title = p.get("title", "")
                    body = p.get("body_html", "")
                    tags = p.get("tags", [])

                    # Filter for plants, saplings, fruit trees, and nursery items
                    is_plant = any(
                        kw in title.lower() or kw in str(tags).lower()
                        for kw in ["plant", "tree", "sapling", "grafted", "herb", "tomato", "chilli"]
                    )
                    if not is_plant:
                        continue

                    # Extract price
                    variants = p.get("variants", [])
                    if not variants:
                        continue

                    v = variants[0]
                    try:
                        price = float(v.get("price") or 0)
                        compare_price = float(v.get("compare_at_price") or price)
                    except (ValueError, TypeError):
                        continue

                    category = "Indoor/Outdoor Plant"
                    if "grafted" in title.lower() or "fruit" in title.lower():
                        category = "Grafted Fruit Plant"
                    elif "tomato" in title.lower() or "herb" in title.lower() or "chilli" in title.lower():
                        category = "Vegetable / Herb Plant"

                    records.append({
                        "name": title.strip(),
                        "category": category,
                        "variety": v.get("title") or "Standard",
                        "plant_stage": "Potted Plant / Sapling",
                        "unit": "per pot/unit",
                        "price": price,
                        "compare_at_price": compare_price,
                        "currency": "INR",
                        "vendor": "PlantsGuru",
                        "location": "India (Online Delivery)",
                        "product_url": f"https://www.plantsguru.com/products/{p.get('handle')}",
                        "scraped_date": today_str,
                        "source": "plantsguru_catalog",
                    })
                logger.info(f"PlantsGuru scraped: {len(records)} plant items.")
        except Exception as e:
            logger.error(f"Error scraping PlantsGuru: {e}")
        return records

    def scrape_trustbasket_plants(self) -> List[Dict[str, Any]]:
        """Scrape live nursery plants and seedling trays from TrustBasket."""
        records = []
        today_str = date.today().isoformat()
        url = "https://www.trustbasket.com/products.json?limit=250"

        try:
            resp = self.session.get(url, timeout=20)
            if resp.status_code == 200:
                products = resp.json().get("products", [])
                for p in products:
                    p_type = p.get("product_type", "")
                    title = p.get("title", "")
                    if p_type == "Plants" or "seedling cup" in title.lower() or "seedling" in title.lower():
                        variants = p.get("variants", [])
                        if not variants:
                            continue
                        v = variants[0]
                        try:
                            price = float(v.get("price") or 0)
                        except (ValueError, TypeError):
                            continue

                        records.append({
                            "name": title.strip(),
                            "category": "Live Plant" if p_type == "Plants" else "Nursery Propagation Supplies",
                            "variety": v.get("title") or "Standard",
                            "plant_stage": "Potted / Seedling Container",
                            "unit": "per unit/pack",
                            "price": price,
                            "currency": "INR",
                            "vendor": "TrustBasket",
                            "location": "India (Online Delivery)",
                            "product_url": f"https://www.trustbasket.com/products/{p.get('handle')}",
                            "scraped_date": today_str,
                            "source": "trustbasket_catalog",
                        })
                logger.info(f"TrustBasket scraped: {len(records)} plant/nursery items.")
        except Exception as e:
            logger.error(f"Error scraping TrustBasket plants: {e}")
        return records

    def scrape_all(self) -> List[Dict[str, Any]]:
        """Run all nursery plant and sapling scrapers."""
        all_plants = []
        all_plants.extend(self.scrape_commercial_benchmarks())
        all_plants.extend(self.scrape_plantsguru())
        all_plants.extend(self.scrape_trustbasket_plants())
        logger.info(f"Total nursery plant records gathered: {len(all_plants)}")
        return all_plants
