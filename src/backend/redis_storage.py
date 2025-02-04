from typing import Optional

import redis as redis

from src.backend.base import Features, OnlineStorageBackend
from src.settings import REDIS_HOST, REDIS_PORT


class RedisStorage(OnlineStorageBackend):
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT):
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    def set_features(self, features: Features) -> bool:
        entity_id = features.id
        last_features = self.get_features(entity_id)
        if not features.is_later_than(last_features):
            return False

        self.client.set(entity_id, features.model_dump_json())

        return True

    def get_features(self, entity_id: str) -> Optional[Features]:
        json_string: Optional[str] = self.client.get(entity_id)  # type:ignore
        if json_string is None:
            return None

        return Features.model_validate_json(json_string)

    def is_alive(self) -> bool:
        try:
            self.client.ping()
            return True
        except redis.ConnectionError:
            return False

    def clean(self):
        self.client.flushdb()

    def close(self):
        self.client.close()
