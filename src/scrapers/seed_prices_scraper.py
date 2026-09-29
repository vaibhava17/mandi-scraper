"""
Seed Prices Scraper (Vegetables, Hybrids & OP Seeds in India).
Pulls commercial seed catalog rates, pack weights, MRP, and discounted prices.
"""

import os
import logging
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, date

logger = logging.getLogger("mandi_scraper.scrapers.seeds")

# Verified Commercial Hybrid Seed Reference Benchmarks (per packet/acre inputs)
COMMERCIAL_HYBRID_SEEDS_BENCHMARKS = [
    {
        "title": "Syngenta Viraja (TO-7414) F1 Hybrid Tomato Seeds",
        "crop": "Tomato",
        "variety": "Viraja (TO-7414)",
        "brand": "Syngenta India Ltd.",
        "seed_type": "F1 Hybrid",
        "pack_size": "3000 seeds",
        "price": 755.00,
        "mrp": 910.00,
        "yield_potential": "30-40 Tons/Acre",
        "seed_rate_per_acre": "80-100 grams",
        "vendor": "AgriBegri / Syngenta Direct",
    },
    {
        "title": "Syngenta Saaho (TO-3251) F1 Hybrid Tomato Seeds",
        "crop": "Tomato",
        "variety": "Saaho (TO-3251)",
        "brand": "Syngenta India Ltd.",
        "seed_type": "F1 Hybrid",
        "pack_size": "3000 seeds",
        "price": 795.00,
        "mrp": 960.00,
        "yield_potential": "35-45 Tons/Acre",
        "seed_rate_per_acre": "80-100 grams",
        "vendor": "AgriBegri / Syngenta Direct",
    },
    {
        "title": "Seminis (Bayer) Abhinav F1 Hybrid Tomato Seeds",
        "crop": "Tomato",
        "variety": "Abhinav",
        "brand": "Bayer Seminis",
        "seed_type": "F1 Hybrid",
        "pack_size": "10 grams (~3500 seeds)",
        "price": 820.00,
        "mrp": 990.00,
        "yield_potential": "35-40 Tons/Acre",
        "seed_rate_per_acre": "80-100 grams",
        "vendor": "National Seeds Dealer Network",
    },
    {
        "title": "Namdhari Seeds NS 501 F1 Hybrid Tomato Seeds",
        "crop": "Tomato",
        "variety": "NS 501",
        "brand": "Namdhari Seeds",
        "seed_type": "F1 Hybrid",
        "pack_size": "10 grams",
        "price": 680.00,
        "mrp": 850.00,
        "yield_potential": "30-38 Tons/Acre",
        "seed_rate_per_acre": "80-100 grams",
        "vendor": "Namdhari Hybrid Seeds",
    },
    {
        "title": "VNR 332 Hybrid Green Chilli Seeds",
        "crop": "Chilli",
        "variety": "VNR 332",
        "brand": "VNR Seeds",
        "seed_type": "F1 Hybrid",
        "pack_size": "10 grams",
        "price": 540.00,
        "mrp": 690.00,
        "yield_potential": "12-15 Tons/Acre (Green)",
        "seed_rate_per_acre": "60-80 grams",
        "vendor": "VNR Agri Network",
    },
    {
        "title": "Syngenta Sitara F1 Hybrid Hot Pepper / Chilli Seeds",
        "crop": "Chilli",
        "variety": "Sitara",
        "brand": "Syngenta India Ltd.",
        "seed_type": "F1 Hybrid",
        "pack_size": "10 grams",
        "price": 590.00,
        "mrp": 740.00,
        "yield_potential": "14-18 Tons/Acre",
        "seed_rate_per_acre": "60-80 grams",
        "vendor": "AgriBegri / Syngenta Direct",
    },
    {
        "title": "VNR 212 F1 Hybrid Brinjal Seeds",
        "crop": "Brinjal",
        "variety": "VNR 212",
        "brand": "VNR Seeds",
        "seed_type": "F1 Hybrid",
        "pack_size": "10 grams",
        "price": 420.00,
        "mrp": 550.00,
        "yield_potential": "25-30 Tons/Acre",
        "seed_rate_per_acre": "100-120 grams",
        "vendor": "VNR Agri Network",
    },
    {
        "title": "Syngenta Indra F1 Hybrid Capsicum Seeds",
        "crop": "Capsicum",
        "variety": "Indra",
        "brand": "Syngenta India Ltd.",
        "seed_type": "F1 Hybrid",
        "pack_size": "10 grams (~1500 seeds)",
        "price": 1450.00,
        "mrp": 1780.00,
        "yield_potential": "40-50 Tons/Acre (Protected)",
        "seed_rate_per_acre": "160-200 grams",
        "vendor": "Syngenta Commercial Distribution",
    },
]


class SeedPricesScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })

    def scrape_commercial_benchmarks(self) -> List[Dict[str, Any]]:
        """Return standardized commercial seed benchmarks."""
        today_str = date.today().isoformat()
        records = []
        for b in COMMERCIAL_HYBRID_SEEDS_BENCHMARKS:
            records.append({
                **b,
                "currency": "INR",
                "scraped_date": today_str,
                "source": "reference_benchmark",
                "is_reference": True,
            })
        return records

    def scrape_trustbasket_seeds(self) -> List[Dict[str, Any]]:
        """Scrape live seed catalog from TrustBasket across pages."""
        records = []
        today_str = date.today().isoformat()

        for page in [2, 3, 4]:
            url = f"https://www.trustbasket.com/products.json?limit=250&page={page}"
            try:
                resp = self.session.get(url, timeout=20)
                if resp.status_code == 200:
                    products = resp.json().get("products", [])
                    for p in products:
                        p_type = p.get("product_type", "")
                        title = p.get("title", "")
                        if p_type == "Seeds" or "seed" in title.lower():
                            variants = p.get("variants", [])
                            if not variants:
                                continue
                            v = variants[0]
                            try:
                                price = float(v.get("price") or 0)
                                compare_price = float(v.get("compare_at_price") or price)
                            except (ValueError, TypeError):
                                continue

                            # Detect crop
                            crop = "Vegetable Seeds"
                            t_lower = title.lower()
                            if "tomato" in t_lower:
                                crop = "Tomato"
                            elif "chilli" in t_lower or "chili" in t_lower:
                                crop = "Chilli"
                            elif "onion" in t_lower:
                                crop = "Onion"
                            elif "gourd" in t_lower:
                                crop = "Gourd"
                            elif "marigold" in t_lower or "flower" in t_lower:
                                crop = "Floriculture"

                            seed_type = "Hybrid" if "hybrid" in t_lower else "Open Pollinated (OP)"

                            records.append({
                                "title": title.strip(),
                                "crop": crop,
                                "variety": v.get("title") or "Standard",
                                "brand": "TrustBasket",
                                "seed_type": seed_type,
                                "pack_size": "Standard Retail Pack",
                                "price": price,
                                "mrp": compare_price,
                                "currency": "INR",
                                "vendor": "TrustBasket",
                                "product_url": f"https://www.trustbasket.com/products/{p.get('handle')}",
                                "scraped_date": today_str,
                                "source": "trustbasket_catalog",
                            })
            except Exception as e:
                logger.error(f"Error scraping TrustBasket seeds page {page}: {e}")

        logger.info(f"TrustBasket scraped: {len(records)} seed items.")
        return records

    def scrape_agribegri_seeds(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Scrape live commercial hybrid vegetable and flower seeds from AgriBegri via sitemap + JSON-LD."""
        records = []
        today_str = date.today().isoformat()
        sitemap_url = "https://agribegri.com/products-sitemap.xml"

        try:
            r = self.session.get(sitemap_url, timeout=20)
            if r.status_code != 200:
                logger.warning(f"Failed to fetch AgriBegri sitemap: status {r.status_code}")
                return records

            # Extract seed product URLs
            import re
            import bs4
            urls = re.findall(r"<loc>(https://agribegri\.com/products/[^<]+seeds[^<]*\.php)</loc>", r.text)
            logger.info(f"Found {len(urls)} seed product URLs in AgriBegri sitemap.")

            # Filter for commercial vegetable and field crops
            priority_crops = ["chilli", "tomato", "okra", "cauliflower", "cabbage", "cucumber", "mustard", "peas", "gourd", "marigold"]
            filtered_urls = []
            for u in urls:
                if any(c in u.lower() for c in priority_crops):
                    filtered_urls.append(u)
                if len(filtered_urls) >= limit:
                    break

            for u in filtered_urls:
                try:
                    resp = self.session.get(u, timeout=15)
                    if resp.status_code != 200:
                        continue
                    soup = bs4.BeautifulSoup(resp.text, "html.parser")
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            data = json.loads(script.string or "")
                            if data.get("@type") == "Product":
                                title = data.get("name", "").strip()
                                brand = data.get("brand", {}).get("name", "AgriBegri")
                                t_lower = title.lower()

                                # Detect crop category
                                crop = "Vegetable Seeds"
                                for c in priority_crops:
                                    if c in t_lower:
                                        crop = c.capitalize()
                                        break

                                seed_type = "F1 Hybrid" if "hybrid" in t_lower or "f1" in t_lower else "Commercial Variety"

                                offers = data.get("offers", [])
                                if isinstance(offers, dict):
                                    offers = [offers]

                                for o in offers:
                                    try:
                                        price = float(o.get("price") or 0)
                                        if price <= 0:
                                            continue
                                        sku = o.get("sku") or "Standard Pack"
                                        records.append({
                                            "title": title,
                                            "crop": crop,
                                            "variety": title.split("-")[0].strip(),
                                            "brand": brand,
                                            "seed_type": seed_type,
                                            "pack_size": sku,
                                            "price": price,
                                            "mrp": price,
                                            "currency": "INR",
                                            "vendor": "AgriBegri",
                                            "product_url": u,
                                            "scraped_date": today_str,
                                            "source": "agribegri_live",
                                            "is_reference": False,
                                        })
                                    except (ValueError, TypeError):
                                        continue
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"Error scraping AgriBegri product {u}: {e}")

            logger.info(f"AgriBegri scraped: {len(records)} live commercial seed items.")
        except Exception as e:
            logger.error(f"Error in AgriBegri seed scraper: {e}")

        return records

    def scrape_all(self) -> List[Dict[str, Any]]:
        """Run all seed price scrapers."""
        all_seeds = []
        all_seeds.extend(self.scrape_agribegri_seeds())
        all_seeds.extend(self.scrape_trustbasket_seeds())
        all_seeds.extend(self.scrape_commercial_benchmarks())
        logger.info(f"Total seed records gathered: {len(all_seeds)}")
        return all_seeds
