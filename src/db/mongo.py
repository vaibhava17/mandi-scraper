"""
MongoDB Database Interface for Mandi, nursery & seed price scraper.
Manages connection, collection indexes, and upsert operations.
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING, UpdateOne
from pymongo.errors import PyMongoError

logger = logging.getLogger("mandi_scraper.db")

DEFAULT_MONGO_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
DEFAULT_DB_NAME = os.getenv("MONGODB_DB", "mandi_scraper")


class AgriDatabase:
    def __init__(self, uri: str = DEFAULT_MONGO_URI, db_name: str = DEFAULT_DB_NAME):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[db_name]
        self.mandi = self.db["mandi_prices"]
        self.plants = self.db["nursery_plants"]
        self.seeds = self.db["seed_prices"]
        self.summaries = self.db["daily_summaries"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Create indexes for high-speed analytical queries and deduplication."""
        try:
            # Mandi indexes
            self.mandi.create_index([("commodity", ASCENDING), ("arrival_date", DESCENDING)])
            self.mandi.create_index([("state", ASCENDING), ("commodity", ASCENDING)])
            self.mandi.create_index(
                [
                    ("state", ASCENDING),
                    ("district", ASCENDING),
                    ("market", ASCENDING),
                    ("commodity", ASCENDING),
                    ("variety", ASCENDING),
                    ("arrival_date", ASCENDING),
                ],
                unique=True,
                name="uniq_mandi_record",
            )

            # Nursery plant indexes
            self.plants.create_index([("category", ASCENDING), ("scraped_date", DESCENDING)])
            self.plants.create_index([("name", ASCENDING), ("vendor", ASCENDING), ("scraped_date", ASCENDING)], unique=True)

            # Seed prices indexes
            self.seeds.create_index([("crop", ASCENDING), ("scraped_date", DESCENDING)])
            self.seeds.create_index([("title", ASCENDING), ("vendor", ASCENDING), ("scraped_date", ASCENDING)], unique=True)

            # Summary index
            self.summaries.create_index([("date", DESCENDING)], unique=True)
            logger.info("MongoDB collections and indexes initialized.")
        except Exception as e:
            logger.warning(f"Error ensuring indexes (may already exist): {e}")

    def upsert_mandi_records(self, records: List[Dict[str, Any]]) -> int:
        """Batch upsert mandi records to prevent duplicates."""
        if not records:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for r in records:
            filt = {
                "state": r.get("state"),
                "district": r.get("district"),
                "market": r.get("market"),
                "commodity": r.get("commodity"),
                "variety": r.get("variety"),
                "arrival_date": r.get("arrival_date"),
            }
            doc = {**r, "updated_at": now}
            if "created_at" not in doc:
                doc["created_at"] = now
            ops.append(UpdateOne(filt, {"$set": doc}, upsert=True))

        try:
            res = self.mandi.bulk_write(ops, ordered=False)
            return (res.upserted_count or 0) + (res.modified_count or 0)
        except PyMongoError as e:
            logger.error(f"Failed to upsert mandi records: {e}")
            return 0

    def upsert_plants_records(self, records: List[Dict[str, Any]]) -> int:
        """Batch upsert nursery plant records."""
        if not records:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for r in records:
            filt = {
                "name": r.get("name"),
                "vendor": r.get("vendor"),
                "scraped_date": r.get("scraped_date"),
            }
            doc = {**r, "updated_at": now}
            if "created_at" not in doc:
                doc["created_at"] = now
            ops.append(UpdateOne(filt, {"$set": doc}, upsert=True))

        try:
            res = self.plants.bulk_write(ops, ordered=False)
            return (res.upserted_count or 0) + (res.modified_count or 0)
        except PyMongoError as e:
            logger.error(f"Failed to upsert nursery plant records: {e}")
            return 0

    def upsert_seeds_records(self, records: List[Dict[str, Any]]) -> int:
        """Batch upsert seed catalog records."""
        if not records:
            return 0
        ops = []
        now = datetime.now(timezone.utc)
        for r in records:
            filt = {
                "title": r.get("title"),
                "vendor": r.get("vendor"),
                "scraped_date": r.get("scraped_date"),
            }
            doc = {**r, "updated_at": now}
            if "created_at" not in doc:
                doc["created_at"] = now
            ops.append(UpdateOne(filt, {"$set": doc}, upsert=True))

        try:
            res = self.seeds.bulk_write(ops, ordered=False)
            return (res.upserted_count or 0) + (res.modified_count or 0)
        except PyMongoError as e:
            logger.error(f"Failed to upsert seed records: {e}")
            return 0

    def save_summary(self, summary_data: Dict[str, Any]):
        """Save daily aggregated summary."""
        date_str = summary_data.get("date")
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        self.summaries.update_one(
            {"date": date_str},
            {"$set": {**summary_data, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
