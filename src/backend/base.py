from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

import pandas as pd
from pydantic import BaseModel


class Features(BaseModel):
    customer_id: int
    purchase_value: float
    loyalty_score: float
    purchase_timestamp: datetime

    @property
    def id(self) -> str:
        return str(self.customer_id)

    @property
    def timestamp(self) -> datetime:
        return self.purchase_timestamp

    def is_later_than(self, other: Optional["Features"]) -> bool:
        return other is None or self.timestamp >= other.timestamp


class FeatureQuery(BaseModel):
    start_time: datetime
    end_time: datetime


class OnlineStorageBackend(ABC):
    @abstractmethod
    def set_features(self, feature: Features) -> bool:
        """Store a single feature value."""
        pass

    @abstractmethod
    def get_features(self, entity_id: str) -> Optional[Features]:
        """Retrieve latest feature values."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Liveliness probe."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass


class OfflineStorageBackend(ABC):
    @abstractmethod
    def store_features(self, features: List[Features]) -> None:
        """Store multiple feature values."""
        pass

    @abstractmethod
    def get_historical_features(self, query: FeatureQuery) -> pd.DataFrame:
        """Retrieve historical feature values."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Liveliness probe."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean up resources."""
        pass


class FeatureTransformation(Protocol):
    def transform(self, event: Dict[str, Any]) -> List[Features]:
        """Transform raw event into features."""
        pass
