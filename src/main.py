#!/usr/bin/env python3
"""
Mandi Scraper: Unified Market Scraper & Analytics Engine.
Scrapes Mandi Wholesale Prices, Nursery Plant & Sapling Rates, and Seed Catalogs across India.
Persists data to MongoDB and publishes daily operational briefs.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so 'src' can be imported anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logging
import argparse
from datetime import datetime, timezone
import requests

from src.db import get_database
from src.scrapers.mandi_scraper import MandiScraper
from src.scrapers.nursery_plants_scraper import NurseryPlantsScraper
from src.scrapers.seed_prices_scraper import SeedPricesScraper
from src.analytics.summary_generator import generate_daily_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("mandi_scraper.main")


def send_whatsapp_summary(summary_text: str):
    """Optional direct dispatch to WhatsApp bridge if configured."""
    bridge_url = os.getenv("WHATSAPP_BRIDGE_URL", "http://127.0.0.1:3000/send")
    target_chat = os.getenv("WHATSAPP_TARGET_CHAT", "")

    try:
        payload = {
            "chatId": target_chat,
            "message": summary_text,
        }
        res = requests.post(bridge_url, json=payload, timeout=10)
        if res.status_code == 200:
            logger.info("Daily summary successfully posted to WhatsApp bridge.")
        else:
            logger.warning(f"WhatsApp bridge returned status {res.status_code}")
    except Exception as e:
        logger.debug(f"WhatsApp bridge send skipped or unavailable: {e}")


def main():
    parser = argparse.ArgumentParser(description="Mandi, nursery & seed price scraper")
    parser.add_argument("--dry-run", action="store_true", help="Scrape without persisting to DB")
    parser.add_argument("--notify-whatsapp", action="store_true", help="Push summary directly to WhatsApp")
    args = parser.parse_args()

    logger.info("=== Starting Mandi Scraper Daily Run ===")

    # 1. Initialize DB
    db = None
    if not args.dry_run:
        try:
            db = get_database()
            logger.info(f"Connected to {type(db).__name__} successfully.")
        except Exception as e:
            logger.error(f"Database connection failed: {e}. Exiting.")
            sys.exit(1)

    # 2. Run Mandi Scraper
    logger.info("Scraping Mandi Vegetable Wholesale Rates...")
    mandi_scraper = MandiScraper()
    mandi_records = mandi_scraper.scrape_all()
    logger.info(f"Retrieved {len(mandi_records)} mandi records.")

    # 3. Run Nursery Plants & Saplings Scraper
    logger.info("Scraping Nursery Plants & Sapling Rate Cards...")
    plants_scraper = NurseryPlantsScraper()
    plant_records = plants_scraper.scrape_all()
    logger.info(f"Retrieved {len(plant_records)} plant/sapling records.")

    # 4. Run Seed Prices Scraper
    logger.info("Scraping Vegetable Seed Catalogs & Input Costs...")
    seeds_scraper = SeedPricesScraper()
    seed_records = seeds_scraper.scrape_all()
    logger.info(f"Retrieved {len(seed_records)} seed records.")

    # 5. Persist to MongoDB
    if db and not args.dry_run:
        logger.info("Persisting datasets...")
        m_count = db.upsert_mandi_records(mandi_records)
        p_count = db.upsert_plants_records(plant_records)
        s_count = db.upsert_seeds_records(seed_records)
        logger.info(f"Upserted: {m_count} mandi rows, {p_count} plant rows, {s_count} seed rows.")

    # 6. Generate Summary
    logger.info("Generating daily analytics brief...")
    summary_data = generate_daily_summary(mandi_records, plant_records, seed_records)

    if db and not args.dry_run:
        db.save_summary(summary_data)

    # Print summary to stdout (for cron capture and reporting)
    print("\n" + summary_data["text_summary"] + "\n")

    # Optional WhatsApp direct push
    if args.notify_whatsapp:
        send_whatsapp_summary(summary_data["text_summary"])

    logger.info("=== Mandi Scraper Run Completed Successfully ===")


if __name__ == "__main__":
    main()
