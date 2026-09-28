"""
Mandi Prices Scraper (All States & Vegetables in India).
Pulls daily wholesale prices from Agmarknet / OGD Data.gov.in.
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, date

logger = logging.getLogger("mandi_scraper.scrapers.mandi")

DEFAULT_COMMODITIES = [
    "Tomato",
    "Onion",
    "Potato",
    "Green Chilli",
    "Chilli Red",
    "Brinjal",
    "Cabbage",
    "Cauliflower",
    "Capsicum",
    "Cucumber",
    "Bitter Gourd",
    "Bottle Gourd",
    "Peas Wet",
    "Bhindi(Ladies Finger)",
    "Ginger(Green)",
    "Garlic",
]

DEFAULT_STATES = [
    "Maharashtra",
    "Uttar Pradesh",
    "Punjab",
    "Madhya Pradesh",
    "Karnataka",
    "Gujarat",
    "Haryana",
    "Rajasthan",
    "West Bengal",
    "Tamil Nadu",
    "Andhra Pradesh",
    "Telangana",
    "Delhi",
]


class MandiScraper:
    def __init__(self, datagov_api_key: Optional[str] = None):
        self.api_key = datagov_api_key or os.getenv("DATAGOV_API_KEY")
        self.public_mirror_url = "https://mandi-api.onrender.com/v1/prices"
        self.ogd_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "mandi-scraper/1.0 (+https://github.com/vaibhava17/mandi-scraper)",
            "Accept": "application/json",
        })

    def fetch_from_public_mirror(
        self, state: Optional[str] = None, commodity: Optional[str] = None, limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Fetch from keyless community Agmarknet mirror."""
        params: Dict[str, Any] = {"limit": limit}
        if state:
            params["state"] = state
        if commodity:
            params["commodity"] = commodity

        try:
            resp = self.session.get(self.public_mirror_url, params=params, timeout=20)
            if resp.status_code == 200:
                payload = resp.json()
                raw_records = payload.get("data", [])
                logger.info(f"Mirror returned {len(raw_records)} records for state={state}, commodity={commodity}")
                return self._normalize_mirror_records(raw_records)
            else:
                logger.warning(f"Public mirror returned status {resp.status_code}")
        except Exception as e:
            logger.error(f"Error calling public mandi mirror: {e}")
        return []

    def fetch_from_ogd(
        self, state: Optional[str] = None, commodity: Optional[str] = None, limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Fetch directly from official data.gov.in API if API key is configured."""
        if not self.api_key:
            return []

        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        if state:
            params["filters[state]"] = state
        if commodity:
            params["filters[commodity]"] = commodity

        try:
            resp = self.session.get(self.ogd_url, params=params, timeout=25)
            if resp.status_code == 200:
                payload = resp.json()
                records = payload.get("records", [])
                logger.info(f"OGD returned {len(records)} records for state={state}, commodity={commodity}")
                return self._normalize_ogd_records(records)
        except Exception as e:
            logger.error(f"Error calling OGD API: {e}")
        return []

    def _normalize_mirror_records(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for r in raw_records:
            try:
                min_p = float(r.get("min_price") or 0)
                max_p = float(r.get("max_price") or 0)
                modal_p = float(r.get("modal_price") or 0)
                kg_price = round(modal_p / 100.0, 2) if modal_p > 0 else 0.0

                arr_date = str(r.get("arrival_date") or "").strip()
                if not arr_date:
                    arr_date = date.today().isoformat()

                normalized.append({
                    "state": str(r.get("state") or "").strip(),
                    "district": str(r.get("district") or "").strip(),
                    "market": str(r.get("market") or "").strip(),
                    "commodity": str(r.get("commodity") or "").strip(),
                    "variety": str(r.get("variety") or "Local").strip(),
                    "grade": str(r.get("grade") or "FAQ").strip(),
                    "min_price": min_p,
                    "max_price": max_p,
                    "modal_price": modal_p,
                    "price_per_kg": kg_price,
                    "arrival_date": arr_date,
                    "source": "agmarknet_mirror",
                })
            except Exception as ex:
                logger.debug(f"Skipping malformed mirror record: {ex}")
        return normalized

    def _normalize_ogd_records(self, raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for r in raw_records:
            try:
                min_p = float(r.get("min_price") or r.get("Min Price") or 0)
                max_p = float(r.get("max_price") or r.get("Max Price") or 0)
                modal_p = float(r.get("modal_price") or r.get("Modal Price") or 0)
                kg_price = round(modal_p / 100.0, 2) if modal_p > 0 else 0.0

                arr_date = str(r.get("arrival_date") or r.get("Arrival_Date") or date.today().isoformat()).strip()

                normalized.append({
                    "state": str(r.get("state") or r.get("State") or "").strip(),
                    "district": str(r.get("district") or r.get("District") or "").strip(),
                    "market": str(r.get("market") or r.get("Market") or "").strip(),
                    "commodity": str(r.get("commodity") or r.get("Commodity") or "").strip(),
                    "variety": str(r.get("variety") or r.get("Variety") or "Local").strip(),
                    "grade": str(r.get("grade") or r.get("Grade") or "FAQ").strip(),
                    "min_price": min_p,
                    "max_price": max_p,
                    "modal_price": modal_p,
                    "price_per_kg": kg_price,
                    "arrival_date": arr_date,
                    "source": "data.gov.in",
                })
            except Exception as ex:
                logger.debug(f"Skipping malformed OGD record: {ex}")
        return normalized

    def scrape_all(self, commodities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scrape latest mandi prices across target commodities and states."""
        targets = commodities or DEFAULT_COMMODITIES
        results: List[Dict[str, Any]] = []

        logger.info(f"Starting Mandi Scraper for {len(targets)} commodities...")
        for commodity in targets:
            # Try OGD if API key configured, otherwise mirror
            data = []
            if self.api_key:
                data = self.fetch_from_ogd(commodity=commodity, limit=200)

            if not data:
                data = self.fetch_from_public_mirror(commodity=commodity, limit=200)

            results.extend(data)

        logger.info(f"Mandi scrape completed. Total records gathered: {len(results)}")
        return results
