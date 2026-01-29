"""
Copyright (c) 2025 Faustino Lopez Ramos.
For licensing information, see the LICENSE file in the project root
"""
from typing import Any, Dict, Optional, List
from queue import Queue, Empty
from datetime import datetime, timezone, timedelta
import threading
import time

from loguru import logger  # type: ignore


class PooledConnection:
    """Wrapper for a pooled connection with metadata."""

    def __init__(self, connection: Any, connection_id: str):
        """Initialize pooled connection."""
        self.connection = connection
        self.connection_id = connection_id
        self.created_at = datetime.now(timezone.utc)
        self.last_used_at = self.created_at
        self.use_count = 0
        self.is_available = True

    def mark_used(self) -> None:
        """Mark connection as used."""
        self.last_used_at = datetime.now(timezone.utc)
        self.use_count += 1

    def is_stale(self, max_age_seconds: int) -> bool:
        """Check if connection is stale."""
        age = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return age > max_age_seconds

    def is_idle(self, idle_threshold_seconds: int) -> bool:
        """Check if connection is idle."""
        idle_time = (datetime.now(timezone.utc) - self.last_used_at).total_seconds()
        return idle_time > idle_threshold_seconds


class ConnectionPool:
    """Thread-safe connection pool for managing reusable connections."""

    def __init__(
        self,
        pool_name: str,
        factory_func,
        min_size: int = 1,
        max_size: int = 10,
        max_age_seconds: int = 3600,
        max_idle_seconds: int = 600,
    ):
        """
        Initialize connection pool.
        """
        self.pool_name = pool_name
        self.factory_func = factory_func
        self.min_size = min_size
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.max_idle_seconds = max_idle_seconds

        self._available = Queue()
        self._in_use: Dict[str, PooledConnection] = {}
        self._all_connections: List[PooledConnection] = []
        self._lock = threading.RLock()
        self._connection_counter = 0

        # Initialize minimum connections
        try:
            for _ in range(min_size):
                self._create_connection()
            logger.info(f"ConnectionPool '{pool_name}' initialized with {min_size} connections")
        except Exception as e:
            logger.error(f"Failed to initialize ConnectionPool '{pool_name}': {e}")

    def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new connection."""
        try:
            with self._lock:
                if len(self._all_connections) >= self.max_size:
                    logger.warning(
                        f"Pool '{self.pool_name}' at max size ({self.max_size}), "
                        f"waiting for available connection"
                    )
                    return None

                conn = self.factory_func()
                self._connection_counter += 1
                pooled = PooledConnection(conn, f"{self.pool_name}#{self._connection_counter}")
                self._all_connections.append(pooled)
                logger.debug(f"Created connection {pooled.connection_id}")
                return pooled
        except Exception as e:
            logger.error(f"Failed to create connection in pool '{self.pool_name}': {e}")
            return None

    def get_connection(self, timeout_seconds: float = 5.0) -> Optional[PooledConnection]:
        """Get a connection from the pool."""
        try:
            # Try to get from available queue first
            try:
                pooled = self._available.get(timeout=timeout_seconds)
                # Validate connection is still good
                if not pooled.is_stale(self.max_age_seconds):
                    with self._lock:
                        self._in_use[pooled.connection_id] = pooled
                    pooled.mark_used()
                    logger.debug(f"Reused connection {pooled.connection_id}")
                    return pooled
                else:
                    logger.debug(f"Connection {pooled.connection_id} is stale, creating new one")
                    self._close_connection(pooled)
            except Empty:
                pass

            # No available connection, try to create new one
            with self._lock:
                if len(self._all_connections) < self.max_size:
                    pooled = self._create_connection()
                    if pooled:
                        self._in_use[pooled.connection_id] = pooled
                        pooled.mark_used()
                        logger.debug(f"Created new connection {pooled.connection_id}")
                        return pooled

            # No luck, pool is exhausted
            logger.warning(
                f"ConnectionPool '{self.pool_name}' exhausted, "
                f"waiting for available connection (timeout={timeout_seconds}s)"
            )

            # Wait for connection with exponential backoff
            total_waited = 0.0
            backoff_ms = 100
            while total_waited < timeout_seconds:
                try:
                    pooled = self._available.get(timeout=0.1)
                    if not pooled.is_stale(self.max_age_seconds):
                        with self._lock:
                            self._in_use[pooled.connection_id] = pooled
                        pooled.mark_used()
                        logger.debug(f"Obtained connection {pooled.connection_id} after waiting")
                        return pooled
                    else:
                        self._close_connection(pooled)
                except Empty:
                    total_waited += 0.1
                    time.sleep(min(backoff_ms / 1000.0, timeout_seconds - total_waited))

            logger.error(
                f"Could not obtain connection from pool '{self.pool_name}' within {timeout_seconds}s"
            )
            return None

        except Exception as e:
            logger.error(f"Error getting connection from pool '{self.pool_name}': {e}")
            return None

    def return_connection(self, connection: PooledConnection) -> None:
        """Return connection to pool."""
        try:
            with self._lock:
                if connection.connection_id in self._in_use:
                    del self._in_use[connection.connection_id]

            # Check if connection is still valid
            if connection.is_stale(self.max_age_seconds):
                logger.debug(f"Closing stale connection {connection.connection_id}")
                self._close_connection(connection)
            else:
                self._available.put(connection)
                logger.debug(f"Returned connection {connection.connection_id} to pool")
        except Exception as e:
            logger.error(f"Error returning connection {connection.connection_id}: {e}")
            self._close_connection(connection)

    def _close_connection(self, pooled: PooledConnection) -> None:
        """Close a connection safely."""
        try:
            with self._lock:
                if pooled in self._all_connections:
                    self._all_connections.remove(pooled)

            if hasattr(pooled.connection, "close"):
                pooled.connection.close()
                logger.debug(f"Closed connection {pooled.connection_id}")
        except Exception as e:
            logger.warning(f"Error closing connection {pooled.connection_id}: {e}")

    def close_all(self) -> None:
        """Close all connections in the pool."""
        try:
            with self._lock:
                for pooled in self._all_connections[:]:
                    self._close_connection(pooled)
                self._in_use.clear()
            logger.info(f"Closed all connections in pool '{self.pool_name}'")
        except Exception as e:
            logger.error(f"Error closing all connections in pool '{self.pool_name}': {e}")

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_name": self.pool_name,
                "total_connections": len(self._all_connections),
                "in_use": len(self._in_use),
                "available": self._available.qsize(),
                "min_size": self.min_size,
                "max_size": self.max_size,
            }

    def cleanup_idle_connections(self) -> int:
        """Remove idle connections to save resources."""
        closed_count = 0
        try:
            with self._lock:
                to_remove = []
                for pooled in self._all_connections:
                    if (
                        pooled.connection_id not in self._in_use
                        and pooled.is_idle(self.max_idle_seconds)
                        and len(self._all_connections) > self.min_size
                    ):
                        to_remove.append(pooled)

                for pooled in to_remove:
                    self._close_connection(pooled)
                    closed_count += 1

            if closed_count > 0:
                logger.info(
                    f"Cleaned up {closed_count} idle connections in pool '{self.pool_name}'"
                )
        except Exception as e:
            logger.error(f"Error cleaning up idle connections: {e}")

        return closed_count

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close_all()

    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_pool_stats()
        return (
            f"ConnectionPool(name={stats['pool_name']}, "
            f"total={stats['total_connections']}, "
            f"in_use={stats['in_use']}, "
            f"available={stats['available']})"
        )
