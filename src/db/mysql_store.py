"""
MySQL storage backend for the mandi, nursery & seed price scraper.

Same interface as the MongoDB backend (AgriDatabase), selected with
DATABASE_URL=mysql://user:pass@host:port/dbname (see src/db/__init__.py).

Rows are upserted on their natural key, so re-running a day overwrites that
day's prices instead of duplicating them. Each row also carries a 24-hex
`mongo_id` (ObjectId-compatible), so data written by either backend can be
merged into the same tables. Schema: sql/mysql-schema.sql.
"""

import json
import logging
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

import pymysql
from bson import ObjectId

logger = logging.getLogger("mandi_scraper.db.mysql")

CHUNK = 500

# column -> max length (VARCHAR limits in sql/mysql-schema.sql); strict sql_mode rejects longer values
LIMITS = {
    "mandi_prices": {"state": 60, "district": 80, "market": 150, "commodity": 80, "variety": 80, "grade": 40,
                     "source": 40},
    "nursery_plants": {"vendor": 100, "name": 255, "category": 60, "crop": 60, "variety": 120,
                       "plant_stage": 60, "location": 120, "unit": 40, "currency": 8, "product_url": 500,
                       "source": 60},
    "seed_prices": {"vendor": 100, "title": 255, "brand": 100, "crop": 60, "variety": 255, "seed_type": 60,
                    "pack_size": 60, "seed_rate_per_acre": 60, "yield_potential": 100, "currency": 8,
                    "product_url": 500, "source": 60},
}

MANDI_COLS = ["mongo_id", "arrival_date", "state", "district", "market", "commodity", "variety", "grade",
              "min_price", "max_price", "modal_price", "price_per_kg", "source", "created_at", "updated_at"]
PLANT_COLS = ["mongo_id", "scraped_date", "vendor", "name", "category", "crop", "variety", "plant_stage",
              "location", "unit", "currency", "price", "price_min", "price_max", "product_url", "source",
              "created_at", "updated_at"]
SEED_COLS = ["mongo_id", "scraped_date", "vendor", "title", "brand", "crop", "variety", "seed_type", "pack_size",
             "seed_rate_per_acre", "yield_potential", "currency", "price", "mrp", "product_url", "source",
             "created_at", "updated_at"]
SUMMARY_COLS = ["date", "mongo_id", "total_mandi", "total_plants", "total_seeds", "mandi_highlights",
                "text_summary", "updated_at"]

# never overwritten on re-scrape: the row keeps its first id and creation time
KEEP_ON_UPDATE = {"mongo_id", "created_at"}


def _strip_quotes(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def parse_mysql_url(url: str) -> Dict[str, Any]:
    url = _strip_quotes(url)
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("mysql", "mysql+pymysql"):
        raise ValueError("DATABASE_URL must start with mysql://")
    db = p.path.lstrip("/")
    if not db:
        raise ValueError("DATABASE_URL has no database name")
    return {
        "host": p.hostname or "127.0.0.1",
        "port": p.port or 3306,
        "user": urllib.parse.unquote(p.username or ""),
        "password": urllib.parse.unquote(p.password or ""),
        "database": db,
    }


def _date(v: Any) -> Optional[str]:
    return v[:10] if isinstance(v, str) and len(v) >= 10 else None


def _cut(table: str, col: str, v: Any) -> Any:
    lim = LIMITS.get(table, {}).get(col)
    if lim and isinstance(v, str) and len(v) > lim:
        return v[:lim]
    return v


def _num(v: Any) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f  # NaN -> NULL


class MySQLDatabase:
    def __init__(self, url: Optional[str] = None):
        cfg = parse_mysql_url(url or os.environ["DATABASE_URL"])
        self.db_name = cfg["database"]
        self.conn = pymysql.connect(
            **cfg, charset="utf8mb4", autocommit=False, connect_timeout=10, read_timeout=120, write_timeout=120,
        )
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name IN "
                      "('mandi_prices','nursery_plants','seed_prices','daily_summaries')", (self.db_name,))
            n = c.fetchone()[0]
        if n != 4:
            raise RuntimeError(f"database '{self.db_name}' is missing tables ({n}/4); apply sql/mysql-schema.sql")
        logger.info("MySQL connected (%s), tables present.", self.db_name)

    # ---------------------------------------------------------------- helpers
    def _upsert(self, table: str, cols: Sequence[str], rows: List[List[Any]]) -> int:
        if not rows:
            return 0
        upd = ", ".join(f"{c}=VALUES({c})" for c in cols if c not in KEEP_ON_UPDATE)
        sql = (f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) "
               f"ON DUPLICATE KEY UPDATE {upd}")
        done = 0
        try:
            with self.conn.cursor() as c:
                for i in range(0, len(rows), CHUNK):
                    part = rows[i:i + CHUNK]
                    c.executemany(sql, part)
                    done += len(part)
            self.conn.commit()
        except pymysql.MySQLError:
            self.conn.rollback()
            logger.exception("MySQL upsert into %s failed; rolled back", table)
            raise
        return done

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    # ---------------------------------------------------------------- public API (same as AgriDatabase)
    def upsert_mandi_records(self, records: List[Dict[str, Any]]) -> int:
        now, rows, t = self._now(), [], "mandi_prices"
        for r in records:
            d = _date(r.get("arrival_date"))
            if not d or not r.get("market") or not r.get("commodity"):
                continue
            rows.append([str(ObjectId()), d, _cut(t, "state", r.get("state") or ""),
                         _cut(t, "district", r.get("district") or ""), _cut(t, "market", r.get("market")),
                         _cut(t, "commodity", r.get("commodity")), _cut(t, "variety", r.get("variety") or "Local"),
                         _cut(t, "grade", r.get("grade")), _num(r.get("min_price")), _num(r.get("max_price")),
                         _num(r.get("modal_price")), _num(r.get("price_per_kg")), _cut(t, "source", r.get("source")),
                         now, now])
        return self._upsert(t, MANDI_COLS, rows)

    def upsert_plants_records(self, records: List[Dict[str, Any]]) -> int:
        now, rows, t = self._now(), [], "nursery_plants"
        for r in records:
            d = _date(r.get("scraped_date"))
            if not d or not r.get("name") or not r.get("vendor"):
                continue
            rows.append([str(ObjectId()), d] + [_cut(t, c, r.get(c)) for c in
                        ("vendor", "name", "category", "crop", "variety", "plant_stage", "location", "unit",
                         "currency")]
                        + [_num(r.get("price")), _num(r.get("price_min")), _num(r.get("price_max")),
                           _cut(t, "product_url", r.get("product_url")), _cut(t, "source", r.get("source")),
                           now, now])
        return self._upsert(t, PLANT_COLS, rows)

    def upsert_seeds_records(self, records: List[Dict[str, Any]]) -> int:
        now, rows, t = self._now(), [], "seed_prices"
        for r in records:
            d = _date(r.get("scraped_date"))
            if not d or not r.get("title") or not r.get("vendor"):
                continue
            rows.append([str(ObjectId()), d] + [_cut(t, c, r.get(c)) for c in
                        ("vendor", "title", "brand", "crop", "variety", "seed_type", "pack_size",
                         "seed_rate_per_acre", "yield_potential", "currency")]
                        + [_num(r.get("price")), _num(r.get("mrp")), _cut(t, "product_url", r.get("product_url")),
                           _cut(t, "source", r.get("source")), now, now])
        return self._upsert(t, SEED_COLS, rows)

    def save_summary(self, summary_data: Dict[str, Any]):
        d = _date(summary_data.get("date")) or datetime.now().strftime("%Y-%m-%d")
        row = [d, str(ObjectId()), summary_data.get("total_mandi_records"), summary_data.get("total_plant_records"),
               summary_data.get("total_seed_records"),
               json.dumps(summary_data.get("mandi_highlights") or {}, ensure_ascii=False, default=str),
               summary_data.get("text_summary"), self._now()]
        self._upsert("daily_summaries", SUMMARY_COLS, [row])

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
