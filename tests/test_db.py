import os
import unittest
from unittest.mock import patch, MagicMock
from src.db.mysql_store import (
    _strip_quotes,
    parse_mysql_url,
    _date,
    _cut,
    _num,
    MySQLDatabase,
)
from src.db import get_database


class TestDatabaseHelpers(unittest.TestCase):
    def test_strip_quotes(self):
        self.assertEqual(_strip_quotes('"test"'), "test")
        self.assertEqual(_strip_quotes("'test'"), "test")
        self.assertEqual(_strip_quotes("test"), "test")
        self.assertEqual(_strip_quotes(""), "")

    def test_parse_mysql_url_valid(self):
        url = "mysql://hp_user:secret_pass@127.0.0.1:3306/hortiprise_agri"
        cfg = parse_mysql_url(url)
        self.assertEqual(cfg["host"], "127.0.0.1")
        self.assertEqual(cfg["port"], 3306)
        self.assertEqual(cfg["user"], "hp_user")
        self.assertEqual(cfg["password"], "secret_pass")
        self.assertEqual(cfg["database"], "hortiprise_agri")

    def test_parse_mysql_url_invalid(self):
        with self.assertRaises(ValueError):
            parse_mysql_url("postgresql://user:pass@localhost/db")

        with self.assertRaises(ValueError):
            parse_mysql_url("mysql://user:pass@localhost/")

    def test_helpers_date_cut_num(self):
        self.assertEqual(_date("2026-10-09T12:00:00Z"), "2026-10-09")
        self.assertIsNone(_date("short"))
        self.assertIsNone(_date(None))

        # Test string truncation
        self.assertEqual(_cut("mandi_prices", "state", "A" * 100), "A" * 60)
        self.assertEqual(_cut("mandi_prices", "unknown_col", "A" * 100), "A" * 100)

        # Test number conversion
        self.assertEqual(_num("123.45"), 123.45)
        self.assertEqual(_num(100), 100.0)
        self.assertIsNone(_num("not_a_num"))
        self.assertIsNone(_num(""))
        self.assertIsNone(_num(None))


class TestDatabaseFactory(unittest.TestCase):
    @patch.dict(os.environ, {"DATABASE_URL": "mysql://u:p@localhost:3306/db"})
    @patch("src.db.mysql_store.MySQLDatabase.__init__", return_value=None)
    def test_get_database_mysql(self, mock_init):
        db = get_database()
        self.assertIsInstance(db, MySQLDatabase)

    @patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False)
    @patch("src.db.mongo.AgriDatabase.__init__", return_value=None)
    def test_get_database_mongo(self, mock_init):
        from src.db.mongo import AgriDatabase
        db = get_database()
        self.assertIsInstance(db, AgriDatabase)


class TestMySQLStoreOperations(unittest.TestCase):
    @patch("src.db.mysql_store.pymysql.connect")
    def test_mysql_upsert_mandi_records(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Mock table count verification query
        mock_cursor.fetchone.return_value = [4]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = MySQLDatabase("mysql://u:p@127.0.0.1:3306/testdb")

        records = [
            {
                "arrival_date": "2026-10-09",
                "market": "Kolar",
                "commodity": "Tomato",
                "state": "Karnataka",
                "district": "Kolar",
                "min_price": 2000,
                "max_price": 3000,
                "modal_price": 2500,
                "price_per_kg": 25.0,
            }
        ]

        count = db.upsert_mandi_records(records)
        self.assertEqual(count, 1)
        mock_conn.commit.assert_called()


if __name__ == "__main__":
    unittest.main()
