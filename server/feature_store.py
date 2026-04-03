"""
Feature Store — Prototype

프로토타입용 in-memory Feature Store.
실서비스에서는 Airbridge DB에서 실시간 lookup하지만,
여기서는 CSV를 시작 시 메모리에 로드하여 동일한 인터페이스 제공.

Lookup key: (app_id, airbridge_uuid)
Returns: 25-element numpy array (15 UA + 10 in-app features)

# Redis 교체 시 변경 사항:
#   1. __init__에서 Redis 클라이언트 연결
#   2. lookup()에서 Redis HGET → numpy 변환
#   3. list_users()에서 Redis SCAN 사용
#   4. user_count에서 Redis DBSIZE 사용
#   인터페이스(메서드 시그니처)는 동일하게 유지
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
    """
    Feature Store interface.
    현재: CSV in-memory (prototype)
    이후: Redis or DynamoDB로 교체 가능 (같은 인터페이스)
    """

    def __init__(self, csv_path: Path = DATA_PATH):
        # --- CSV 구현 ---
        # Redis 교체 시: self.redis = redis.Redis(host=..., port=..., db=0)
        self.df = pd.read_csv(csv_path)
        # Build lookup index: (app_id, airbridge_uuid) -> row index
        self.df['_key'] = self.df['app_id'] + '::' + self.df['airbridge_uuid']
        self._index = dict(zip(self.df['_key'], self.df.index))
        # Pre-compute feature matrix as numpy
        self._features = self.df[ALL_FEATURES].values.astype(np.float64)
        print(f"[FeatureStore] Loaded {len(self.df)} users from {csv_path}")

    def lookup(self, app_id: str, user_id: str) -> Optional[np.ndarray]:
        """
        25-element feature array or None.

        Args:
            app_id: 앱 식별자 (e.g., "ablog")
            user_id: airbridge_uuid

        Returns:
            np.ndarray of shape (25,) if found, None otherwise.
            Order: 15 UA features + 10 in-app features (matches model training order).
        """
        # --- CSV 구현 ---
        # Redis 교체 시: raw = self.redis.hget(f"{app_id}::{user_id}", "features")
        #                return np.frombuffer(raw, dtype=np.float64) if raw else None
        key = f"{app_id}::{user_id}"
        idx = self._index.get(key)
        if idx is None:
            return None
        return self._features[idx]

    def list_users(self, app_id: str) -> list[str]:
        """Return all airbridge_uuids for a given app_id."""
        # Redis 교체 시: SCAN with pattern f"{app_id}::*"
        mask = self.df['app_id'] == app_id
        return self.df.loc[mask, 'airbridge_uuid'].tolist()

    @property
    def user_count(self) -> int:
        """Total number of users across all apps."""
        # Redis 교체 시: self.redis.dbsize()
        return len(self.df)
