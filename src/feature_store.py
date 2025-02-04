import logging
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from src.backend.base import FeatureQuery, Features, FeatureTransformation, OfflineStorageBackend, OnlineStorageBackend
from src.backend.duckdb_storage import DuckDBStorage
from src.backend.redis_storage import RedisStorage
from src.backend.transformations import DefaultTransformation
from src.settings import DATE_FORMAT, TEST_DATA_PATH

logging.basicConfig(level=logging.INFO)  # foramt can be improved with more details
logger = logging.getLogger(__name__)


class FeatureStore:
    def __init__(
        self,
        online_storage: OnlineStorageBackend,
        offline_storage: OfflineStorageBackend,
        transformation: FeatureTransformation,
    ):
        """
        Feature Store with modular storage backends.

        Args:
            online_storage: Storage backend for latest features
            offline_storage: Storage backend for historical features
            transformation: Strategy for transforming events to features
        """
        self.online_storage = online_storage
        self.offline_storage = offline_storage
        self.transformation = transformation

    def ingest_event(self, event: Dict[str, Any]) -> None:
        """Ingest a single event and update features."""
        try:
            features_list = self.transformation.transform(event)

            for features in features_list:
                if not self.online_storage.set_features(features):
                    logger.warning(f"Record with {features.id=} and {features.timestamp=} is not latest")

            self.offline_storage.store_features(features_list)
        except Exception as e:  # Ideally, we want to be more specific and handle duplicates or other errors separately
            logger.error(f"Error ingesting event: {e}")

    def get_latest_features(self, entity_id: str) -> Optional[Features]:
        """Retrieve latest feature values."""
        return self.online_storage.get_features(entity_id)

    def get_historical_features(self, query: FeatureQuery) -> pd.DataFrame:
        """Retrieve historical feature values."""
        return self.offline_storage.get_historical_features(query)

    def is_alive(self) -> bool:
        """Liveliness of feature store"""
        return self.online_storage.is_alive() and self.offline_storage.is_alive()

    def clean(self):
        """Clean data"""
        self.online_storage.clean()
        self.offline_storage.clean()

    def close(self):
        """Clean up resources."""
        self.online_storage.close()
        self.offline_storage.close()


class StorageFactory:
    @staticmethod
    def create_online_storage(storage_type: str = "redis", **kwargs) -> OnlineStorageBackend:
        if storage_type == "redis":
            return RedisStorage(**kwargs)

        raise ValueError(f"Unknown online storage type: {storage_type}")

    @staticmethod
    def create_offline_storage(storage_type: str = "duckdb", **kwargs) -> OfflineStorageBackend:
        if storage_type == "duckdb":
            return DuckDBStorage(**kwargs)

        raise ValueError(f"Unknown offline storage type: {storage_type}")


if __name__ == "__main__":
    try:
        online_storage = StorageFactory.create_online_storage("redis")
        offline_storage = StorageFactory.create_offline_storage("duckdb")
        feature_store = FeatureStore(
            online_storage=online_storage,
            offline_storage=offline_storage,
            transformation=DefaultTransformation(),
        )
        assert feature_store.is_alive()

        df = pd.read_csv(TEST_DATA_PATH)

        for _, row in df.iterrows():
            event = row.to_dict()
            feature_store.ingest_event(event)

        entity_id = "16"
        latest_features = feature_store.get_latest_features(entity_id)
        print(f"Latest features for customer {entity_id}:", latest_features)

        query = FeatureQuery(
            start_time=datetime.strptime("2022-01-01 00:00:00", DATE_FORMAT),
            end_time=datetime.strptime("2022-02-01 00:00:00", DATE_FORMAT),
        )
        historical_features = feature_store.get_historical_features(query)
        print(f"Historical features for {query}:\n", historical_features)

        feature_store.clean()
    finally:
        feature_store.close()
