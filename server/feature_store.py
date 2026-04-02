"""
Feature Store — Prototype

프로토타입용 in-memory Feature Store.
실서비스에서는 Airbridge DB에서 실시간 lookup하지만,
여기서는 CSV를 시작 시 메모리에 로드하여 동일한 인터페이스 제공.

Lookup key: (app_id, airbridge_uuid)
Returns: 25-element numpy array (15 UA + 10 in-app features)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

DATA_PATH = Path(__file__).parent.parent / "data" / "feature_store.csv"

# Feature column order (must match model training order)
UA_FEATURES = [
    'trackinglink_count', 'DA_count', 'SA_count', 'unique_channel_count',
    'channel_entropy', 'last_touch_is_da', 'latency', 'recency',
    'recent_touch_pressure', 'touch_per_latency_hour', 'last1h_touch_count',
    'recent_24h_ratio', 'click_ratio', 'impression_count', 'is_single_touch_install',
]

INAPP_FEATURES = [
    'product_viewed_count', 'user_signin', 'product_addedtocart',
    'deeplink_open', 'home_viewed', 'addtowishlist', 'onboarding',
    'user_signup', 'total_events', 'n_event_types',
]

ALL_FEATURES = UA_FEATURES + INAPP_FEATURES


class FeatureStore:
    """In-memory feature store backed by CSV."""

    def __init__(self, csv_path: Path = DATA_PATH):
        self.df = pd.read_csv(csv_path)
        # Build lookup index: (app_id, airbridge_uuid) → row index
        self.df['_key'] = self.df['app_id'] + '::' + self.df['airbridge_uuid']
        self._index = dict(zip(self.df['_key'], self.df.index))
        # Pre-compute feature matrix as numpy
        self._features = self.df[ALL_FEATURES].values.astype(np.float64)
        print(f"[FeatureStore] Loaded {len(self.df)} users from {csv_path}")

    def lookup(self, app_id: str, airbridge_uuid: str) -> Optional[np.ndarray]:
        """
        Lookup user features by (app_id, airbridge_uuid).

        Returns:
            np.ndarray of shape (25,) if found, None otherwise.
            Order: 15 UA features + 10 in-app features (matches model training order).
        """
        key = f"{app_id}::{airbridge_uuid}"
        idx = self._index.get(key)
        if idx is None:
            return None
        return self._features[idx]

    def list_users(self, app_id: str) -> list[str]:
        """Return all airbridge_uuids for a given app_id."""
        mask = self.df['app_id'] == app_id
        return self.df.loc[mask, 'airbridge_uuid'].tolist()

    @property
    def user_count(self) -> int:
        return len(self.df)
