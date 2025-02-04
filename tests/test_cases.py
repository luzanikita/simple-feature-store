from datetime import datetime

import duckdb
import pandas as pd
import pytest
import redis

from src.backend.base import FeatureQuery
from src.backend.transformations import DefaultTransformation
from src.feature_store import FeatureStore, StorageFactory
from src.settings import TEST_DATA_PATH


@pytest.fixture
def feature_store():
    """Create a real feature store instance"""
    online_storage = StorageFactory.create_online_storage("redis")
    offline_storage = StorageFactory.create_offline_storage("duckdb")
    store = FeatureStore(
        online_storage=online_storage, offline_storage=offline_storage, transformation=DefaultTransformation()
    )
    yield store
    store.clean()
    store.close()


@pytest.fixture
def sample_events():
    """Load sample event data"""
    df = pd.read_csv(TEST_DATA_PATH)

    events = []
    for _, row in df.iterrows():
        event = row.to_dict()
        events.append(event)

    return events


def test_healthcheck(feature_store):
    assert feature_store.is_alive()


def test_latest_event(feature_store):
    """Test handling latest events for single customer"""

    events = [
        {
            "customer_id": 16,
            "purchase_value": 321.84,
            "loyalty_score": 1.46,
            "purchase_timestamp": "2022-01-05 14:37:14",
        },
        {
            "customer_id": 16,
            "purchase_value": 450.00,
            "loyalty_score": 2.5,
            "purchase_timestamp": "2022-02-05 14:37:14",  # later
        },
        {
            "customer_id": 16,
            "purchase_value": 111.11,
            "loyalty_score": 2.22,
            "purchase_timestamp": "2021-01-05 14:37:14",  # earlier
        },
    ]

    for event in events:
        feature_store.ingest_event(event)

    assert feature_store.get_latest_features("16").timestamp == datetime(2022, 2, 5, 14, 37, 14)
    assert (
        feature_store.get_historical_features(
            FeatureQuery(start_time=datetime(2020, 1, 1), end_time=datetime(2025, 1, 1))
        ).shape[0]
        == 3
    )


def test_feature_store_end_to_end(feature_store, sample_events):
    """Test complete flow of ingesting and retrieving features"""
    # Ingest multiple events
    for event in sample_events:
        feature_store.ingest_event(event)

    # Test getting latest features
    latest_features = feature_store.get_latest_features("16")
    assert latest_features.id == "16"
    assert latest_features.purchase_value == 321.84
    assert latest_features.loyalty_score == 1.46
    assert latest_features.purchase_timestamp == datetime(2022, 9, 8, 4, 7, 24)  # Should get most recent

    # Test getting historical features
    query = FeatureQuery(start_time=datetime(2022, 1, 1), end_time=datetime(2022, 2, 1))
    historical_features = feature_store.get_historical_features(query)

    assert historical_features.shape == (20, 4)

    query = FeatureQuery(start_time=datetime(2020, 1, 1), end_time=datetime(2025, 1, 1))
    historical_features = feature_store.get_historical_features(query)

    assert historical_features.query("customer_id == 16").shape[0] == 5
