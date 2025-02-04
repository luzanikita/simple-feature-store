from datetime import datetime
from typing import Any, Dict, List

from src.backend.base import Features, FeatureTransformation
from src.settings import DATE_FORMAT


class DefaultTransformation(FeatureTransformation):
    def transform(self, event: Dict[str, Any]) -> List[Features]:
        return [
            Features(
                customer_id=int(event["customer_id"]),
                purchase_value=float(event["purchase_value"]),
                loyalty_score=float(event["loyalty_score"]),
                purchase_timestamp=datetime.strptime(event["purchase_timestamp"], DATE_FORMAT),
            )
        ]
