from typing import List

import duckdb
import pandas as pd

from src.backend.base import FeatureQuery, Features, OfflineStorageBackend
from src.settings import DUCKDB_PATH


class DuckDBStorage(OfflineStorageBackend):
    def __init__(self, db_path: str = DUCKDB_PATH, batch_size: int = 1000):
        self.conn = duckdb.connect(db_path)
        self._init_tables()
        self.batch_buffer: List[Features] = []
        self.batch_size = batch_size

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS historical_features (
                customer_id INTEGER NOT NULL,
                purchase_timestamp DATETIME NOT NULL,
                purchase_value FLOAT NOT NULL,
                loyalty_score FLOAT NOT NULL,
                PRIMARY KEY (customer_id, purchase_timestamp)

            )
        """)

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_historical_features 
            ON historical_features(customer_id, purchase_timestamp)
        """)

    def store_features(self, features: List[Features]) -> None:
        df = pd.DataFrame(  # noqa: F841
            [f.model_dump() for f in features]
        )

        self.conn.execute("""
            INSERT INTO historical_features (customer_id, purchase_timestamp, purchase_value, loyalty_score)
            SELECT customer_id, purchase_timestamp, purchase_value, loyalty_score
            FROM df
        """)

    def get_historical_features(self, query: FeatureQuery) -> pd.DataFrame:
        return self.conn.execute(
            """
            SELECT 
                customer_id,
                purchase_timestamp,
                purchase_value,
                loyalty_score
            FROM historical_features
            WHERE purchase_timestamp BETWEEN $1 AND $2
            ORDER BY customer_id, purchase_timestamp
        """,
            (query.start_time, query.end_time),
        ).fetchdf()

    def is_alive(self) -> bool:
        try:
            self.conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    def clean(self):
        self.conn.execute("DROP TABLE IF EXISTS historical_features")

    def close(self):
        self.conn.close()
