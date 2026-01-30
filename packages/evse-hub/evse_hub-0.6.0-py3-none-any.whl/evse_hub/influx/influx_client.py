"""Singleton InfluxDB client manager with connection pooling."""
from __future__ import annotations

from influxdb import InfluxDBClient
from requests.exceptions import ConnectionError, Timeout
import logging
from threading import Lock

log = logging.getLogger(__name__)


class InfluxDBConnectionPool:
    """Manages persistent InfluxDB connections."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._ha_client = None
        self._mons_client = None
        self._secrets = None
        self._write_lock = Lock()  # Add lock for write operations
        self._initialized = True
    
    def initialize(self, secrets: dict):
        """Initialize connections with secrets."""
        self._secrets = secrets
        self._connect_ha()
        self._connect_mons()
    
    def _connect_ha(self):
        """Create/recreate HA connection."""
        try:
            if self._ha_client:
                try:
                    self._ha_client.close()
                except Exception:
                    pass
            
            self._ha_client = InfluxDBClient(
                host=self._secrets["ha_ip"],
                port=8086,
                username=self._secrets["ha_influx_username"],
                password=self._secrets["ha_influx_pwd"],
                timeout=5,
            )
            log.info("HA InfluxDB connection established")
        except (ConnectionError, Timeout) as e:
            log.warning("HA InfluxDB unreachable: %s", str(e))
            self._ha_client = None
        except Exception:
            log.exception("Unexpected error creating HA InfluxDB client")
            self._ha_client = None
    
    def _connect_mons(self):
        """Create/recreate mons connection."""
        try:
            if self._mons_client:
                try:
                    self._mons_client.close()
                except Exception:
                    pass
            
            self._mons_client = InfluxDBClient(
                host=self._secrets["mons_ip"],
                port=8086,
                username=self._secrets["mons_influx_username"],
                password=self._secrets["mons_influx_pwd"],
                timeout=5,
            )
            log.info("mons InfluxDB connection established")
        except (ConnectionError, Timeout) as e:
            log.warning("mons InfluxDB unreachable: %s", str(e))
            self._mons_client = None
        except Exception:
            log.exception("Unexpected error creating mons InfluxDB client")
            self._mons_client = None
    
    def get_ha_client(self) -> InfluxDBClient | None:
        """Get HA client, reconnecting if needed."""
        if self._ha_client is None:
            self._connect_ha()
        return self._ha_client
    
    def get_mons_client(self) -> InfluxDBClient | None:
        """Get mons client, reconnecting if needed."""
        if self._mons_client is None:
            self._connect_mons()
        return self._mons_client
    
    def write_ha(self, database: str, payload: dict) -> bool:
        """Write to HA InfluxDB with automatic retry on connection failure."""
        with self._write_lock:  # Protect concurrent writes
            client = self.get_ha_client()
            if client is None:
                return False
            
            try:
                client.switch_database(database)
                client.write_points([payload])
                return True
            except (ConnectionError, Timeout) as e:
                log.warning("HA write failed (connection issue), retrying: %s", str(e))
                self._connect_ha()  # Reconnect
                client = self.get_ha_client()
                if client:
                    try:
                        client.switch_database(database)
                        client.write_points([payload])
                        return True
                    except Exception as e:
                        log.warning("HA write retry failed: %s", str(e))
                return False
            except Exception as e:
                log.warning("Writing to HA influx failed: %s", str(e))
                return False
    
    def write_mons(self, database: str, payload: dict | list) -> bool:
        """Write to mons InfluxDB with automatic retry on connection failure."""
        with self._write_lock:  # Protect concurrent writes
            client = self.get_mons_client()
            if client is None:
                return False
            
            payloads = [payload] if isinstance(payload, dict) else payload
            
            try:
                client.switch_database(database)
                client.write_points(payloads)
                return True
            except (ConnectionError, Timeout) as e:
                log.warning("mons write failed (connection issue), retrying: %s", str(e))
                self._connect_mons()  # Reconnect
                client = self.get_mons_client()
                if client:
                    try:
                        client.switch_database(database)
                        client.write_points(payloads)
                        return True
                    except Exception as e:
                        log.warning("mons write retry failed: %s", str(e))
                return False
            except Exception as e:
                log.warning("Writing to mons influx failed: %s", str(e))
                return False
    
    def close(self):
        """Close all connections."""
        if self._ha_client:
            try:
                self._ha_client.close()
            except Exception:
                pass
        if self._mons_client:
            try:
                self._mons_client.close()
            except Exception:
                pass


# Global instance
pool = InfluxDBConnectionPool()