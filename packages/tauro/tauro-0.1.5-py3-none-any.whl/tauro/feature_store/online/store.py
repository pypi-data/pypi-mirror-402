"""
Copyright (c) 2025 Faustino Lopez Ramos.
"""
import json
import threading
from typing import Any, Dict, List, Optional
from loguru import logger

from tauro.feature_store.base import BaseOnlineStore


class InMemOnlineStore(BaseOnlineStore):
    """Simple in-memory KV store for testing Phase 2 features."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _get_key(self, feature_group: str, entity_keys: Dict[str, Any]) -> str:
        # Create a stable string key from entity keys
        sorted_keys = sorted(entity_keys.items())
        entity_id = ":".join([f"{k}={v}" for k, v in sorted_keys])
        return f"{feature_group}:{entity_id}"

    def get_online_features(
        self,
        feature_group: str,
        entity_keys: Dict[str, Any],
        feature_names: List[str],
    ) -> Dict[str, Any]:
        key = self._get_key(feature_group, entity_keys)
        with self._lock:
            stored_data = self._data.get(key, {})

        # Return only requested features
        return {f: stored_data.get(f) for f in feature_names if f in stored_data}

    def write_online_features(
        self,
        feature_group: str,
        data: List[Dict[str, Any]],
        entity_keys: List[str],
    ) -> None:
        with self._lock:
            for record in data:
                # Extract entity keys for indexing
                e_keys = {k: record.get(k) for k in entity_keys}
                key = self._get_key(feature_group, e_keys)

                # Merge or overwrite record
                if key not in self._data:
                    self._data[key] = {}
                self._data[key].update(record)

        logger.debug(f"Wrote {len(data)} records to InMemOnlineStore for {feature_group}")

    def delete_online_features(
        self,
        feature_group: str,
        entity_keys: Dict[str, Any],
    ) -> None:
        key = self._get_key(feature_group, entity_keys)
        with self._lock:
            self._data.pop(key, None)


class RedisOnlineStore(BaseOnlineStore):
    """Redis backend for high-performance online serving."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.db = config.get("db", 0)
        self.password = config.get("password")
        self._client = None
        self._connected = False

    @property
    def client(self):
        if not self._connected:
            try:
                import redis  # type: ignore

                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                )
                self._connected = True
            except ImportError:
                logger.error("redis-py not installed. Run 'pip install redis'")
                raise
        return self._client

    def _get_key(self, feature_group: str, entity_keys: Dict[str, Any]) -> str:
        sorted_keys = sorted(entity_keys.items())
        entity_id = ":".join([f"{k}={v}" for k, v in sorted_keys])
        return f"tauro:fs:{feature_group}:{entity_id}"

    def get_online_features(
        self,
        feature_group: str,
        entity_keys: Dict[str, Any],
        feature_names: List[str],
    ) -> Dict[str, Any]:
        key = self._get_key(feature_group, entity_keys)
        data = self.client.hgetall(key)
        return {f: data.get(f) for f in feature_names if f in data}

    def write_online_features(
        self,
        feature_group: str,
        data: List[Dict[str, Any]],
        entity_keys: List[str],
    ) -> None:
        pipe = self.client.pipeline()
        for record in data:
            e_keys = {k: record.get(k) for k in entity_keys}
            key = self._get_key(feature_group, e_keys)
            # Remove entity keys from values to save space if needed,
            # but usually they are part of the record
            pipe.hset(key, mapping={k: str(v) for k, v in record.items()})
        pipe.execute()

    def delete_online_features(
        self,
        feature_group: str,
        entity_keys: Dict[str, Any],
    ) -> None:
        key = self._get_key(feature_group, entity_keys)
        self.client.delete(key)


def create_online_store(config: Dict[str, Any]) -> BaseOnlineStore:
    """Factory function for Online Stores."""
    store_type = config.get("type", "in_memory").lower()

    if store_type == "in_memory":
        return InMemOnlineStore(config)
    elif store_type == "redis":
        return RedisOnlineStore(config)
    else:
        logger.warning(f"Unknown online store type '{store_type}', falling back to in_memory")
        return InMemOnlineStore(config)
