"""GeoIP lookup mutator."""

import ipaddress
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import maxminddb
else:
    try:
        import maxminddb
    except ImportError:
        maxminddb = None

from ..cache import CacheManager, LocalCacheManager, RedisCacheManager
from ..exceptions import TQLConfigError
from ..geoip_normalizer import GeoIPNormalizer
from .base import BaseMutator, PerformanceClass


class GeoIPResolver:
    """Handles GeoIP MMDB file detection and loading."""

    def __init__(self, config: Optional[Dict[str, str]] = None):
        if maxminddb is None:
            raise ImportError("maxminddb package is required for GeoIP lookups")

        self.config = config or {}
        self.db_type: Optional[str] = None  # Will be set by _load_mmdb_files
        self.mmdb_type: Optional[str] = None  # Full type identifier (e.g., 'dbip_pro', 'maxmind_lite')
        self.mmdb_readers = self._load_mmdb_files()

    def _load_mmdb_files(self) -> Dict[str, Any]:  # noqa: C901
        """Load MMDB files with smart detection.

        Supported environment variables (in priority order):
        - TQL_GEOIP_DB_PATH: Full path to combined database (City, Country, ASN all-in-one)
        - TQL_GEOIP_DB_CITY_PATH: Path to City database
        - TQL_GEOIP_DB_COUNTRY_PATH: Path to Country database
        - TQL_GEOIP_DB_ASN_PATH: Path to ASN database
        - TQL_GEOIP_MMDB_PATH: Base directory for auto-detection (default: /usr/share/geoip)
        """
        # Check for explicit full DB path first (from config or environment variable)
        db_path = self.config.get("db_path") or os.environ.get("TQL_GEOIP_DB_PATH")
        if db_path:
            # Expand user home directory (~)
            db_path = os.path.expanduser(db_path)
        if db_path and os.path.exists(db_path):
            # Detect DB type from filename
            db_lower = db_path.lower()
            if "dbip" in db_lower or "db-ip" in db_lower:
                self.db_type = "dbip"
                if "lite" in db_lower:
                    self.mmdb_type = "dbip_lite"
                else:
                    self.mmdb_type = "dbip_pro"
            else:
                self.db_type = "maxmind"
                if "lite" in db_lower:
                    self.mmdb_type = "maxmind_lite"
                else:
                    self.mmdb_type = "maxmind_pro"
            return {"full": maxminddb.open_database(db_path)}

        # Check base path for auto-detection
        base_path = self.config.get("base_path", os.environ.get("TQL_GEOIP_MMDB_PATH", "/usr/share/geoip"))
        base_path = os.path.expanduser(base_path)

        # Priority order for database detection
        db_patterns: List[Dict[str, Any]] = [
            # Single file databases (contains all data)
            {"type": "full", "files": ["dbip-full.mmdb"], "vendor": "dbip", "mmdb_type": "dbip_pro"},  # DB-IP paid
            {
                "type": "full",
                "files": ["GeoIP2-City.mmdb"],
                "vendor": "maxmind",
                "mmdb_type": "maxmind_pro",
            },  # MaxMind paid (City includes Country)
            # Multi-file databases (need all files for complete data)
            {
                "type": "multi",
                "files": {"city": "GeoIP2-City.mmdb", "asn": "GeoIP2-ASN.mmdb"},
                "vendor": "maxmind",
                "mmdb_type": "maxmind_pro",
            },  # MaxMind paid (separate)
            {
                "type": "multi",
                "files": {
                    "city": "dbip-city-lite.mmdb",
                    "country": "dbip-country-lite.mmdb",
                    "asn": "dbip-asn-lite.mmdb",
                },
                "vendor": "dbip",
                "mmdb_type": "dbip_lite",
            },  # DB-IP free
            {
                "type": "multi",
                "files": {"city": "GeoLite2-City.mmdb", "asn": "GeoLite2-ASN.mmdb"},
                "vendor": "maxmind",
                "mmdb_type": "maxmind_lite",
            },  # MaxMind free
        ]

        # Try each pattern in priority order
        for pattern in db_patterns:
            if pattern["type"] == "full":
                # Single file contains all data
                for filename in pattern["files"]:
                    path = os.path.join(base_path, filename)
                    if os.path.exists(path):
                        self.db_type = pattern["vendor"]
                        self.mmdb_type = pattern["mmdb_type"]
                        return {"full": maxminddb.open_database(path)}
            else:
                # Multiple files needed - check config, environment variables, then base_path
                readers = {}
                all_found = True
                for db_type, filename in pattern["files"].items():
                    # Priority: config > environment variable > base_path/filename
                    env_var_name = f"TQL_GEOIP_DB_{db_type.upper()}_PATH"
                    path = (
                        self.config.get(f"{db_type}_db")
                        or os.environ.get(env_var_name)
                        or os.path.join(base_path, filename)
                    )
                    # Expand user home directory (~)
                    path = os.path.expanduser(path)
                    if os.path.exists(path):
                        readers[db_type] = maxminddb.open_database(path)
                    else:
                        all_found = False
                        break

                if all_found and readers:
                    self.db_type = pattern["vendor"]
                    self.mmdb_type = pattern["mmdb_type"]
                    return readers

        raise TQLConfigError(
            f"No GeoIP MMDB files found in {base_path}. " f"Supported: DB-IP (paid/free) or MaxMind (GeoIP2/GeoLite2)"
        )

    def lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        """Lookup IP and return raw result."""
        try:
            if "full" in self.mmdb_readers:
                raw_data = self.mmdb_readers["full"].get(ip)
                return raw_data
            else:
                # Combine data from multiple files
                result = {}
                if "city" in self.mmdb_readers:
                    city_data = self.mmdb_readers["city"].get(ip)
                    if city_data:
                        result.update(city_data)
                if "country" in self.mmdb_readers:
                    country_data = self.mmdb_readers["country"].get(ip)
                    if country_data:
                        result.update(country_data)
                if "asn" in self.mmdb_readers:
                    asn_data = self.mmdb_readers["asn"].get(ip)
                    if asn_data:
                        result.update(asn_data)
                return result if result else None
        except Exception:
            return None

    def close(self):
        """Close all MMDB readers."""
        for reader in self.mmdb_readers.values():
            if hasattr(reader, "close"):
                reader.close()


class GeoIPLookupMutator(BaseMutator):
    """
    Mutator that performs GeoIP lookups on IP addresses using MMDB files.
    Returns normalized data following ECS (Elastic Common Schema) conventions.

    Performance Characteristics:
    - In-memory: MODERATE - Local database lookups with caching
    - OpenSearch: SLOW - Post-processing overhead plus database lookups

    Parameters:
        db_path: Path to GeoIP database file
        cache: Enable caching (default: True)
        cache_ttl: Cache TTL in seconds (default: 86400)
        force: Force new lookup even if data exists (default: False)
        save: Save enrichment to record (default: True)
        field: Field name to store results

    Example:
        ip_address | geoip_lookup(cache=true) contains 'US'
    """

    # Class-level cache and resolver
    _cache_manager: Optional[CacheManager] = None
    _geo_resolver: Optional[GeoIPResolver] = None
    _geo_resolvers: Dict[str, GeoIPResolver] = {}

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.is_enrichment = True
        # GeoIP uses local database, so it's moderate in memory
        self.performance_in_memory = PerformanceClass.MODERATE
        # Slower in OpenSearch due to post-processing overhead
        self.performance_opensearch = PerformanceClass.SLOW

    @classmethod
    def initialize_cache(cls, cache_backend: Optional[str] = None):
        """Initialize the cache manager based on configuration."""
        if cache_backend == "redis":
            # Initialize Redis cache
            redis_host = os.environ.get("TQL_REDIS_HOST", "localhost")
            redis_port = int(os.environ.get("TQL_REDIS_PORT", 6379))
            redis_password = os.environ.get("TQL_REDIS_PASSWORD")
            redis_db = int(os.environ.get("TQL_REDIS_DB", 0))

            try:
                import redis  # pylint: disable=import-error

                redis_client = redis.Redis(
                    host=redis_host, port=redis_port, password=redis_password, db=redis_db, decode_responses=True
                )
                # Test connection
                redis_client.ping()
                cls._cache_manager = RedisCacheManager(redis_client)
            except Exception:
                # Fall back to local cache on Redis connection error
                cls._cache_manager = LocalCacheManager()
        elif cache_backend != "none":
            # Default to local cache
            max_size = int(os.environ.get("TQL_CACHE_LOCAL_MAX_SIZE", 10000))
            default_ttl = int(os.environ.get("TQL_CACHE_LOCAL_TTL", 3600))
            cls._cache_manager = LocalCacheManager(max_size=max_size, default_ttl=default_ttl)

    @classmethod
    def get_cache_manager(cls) -> Optional[CacheManager]:
        """Get or create the cache manager."""
        if cls._cache_manager is None:
            cache_backend = os.environ.get("TQL_CACHE_BACKEND", "local")
            cls.initialize_cache(cache_backend)
        return cls._cache_manager

    @classmethod
    def get_geo_resolver(cls, config: Optional[Dict[str, str]] = None) -> GeoIPResolver:
        """Get or create the GeoIP resolver.

        Note: Resolver is cached at class level per unique configuration.
        Config with explicit paths will be cached separately from environment variable configs.
        Environment variable changes require process restart to take effect.
        """
        # Create cache key based on config
        if config is None:
            cache_key = "env_vars"  # Uses environment variables
        else:
            # Use config values as cache key
            cache_key = str(sorted(config.items()))

        # Check if we have a cached resolver for this config
        if not hasattr(cls, "_geo_resolvers"):
            cls._geo_resolvers = {}

        if cache_key not in cls._geo_resolvers:
            cls._geo_resolvers[cache_key] = GeoIPResolver(config)

        return cls._geo_resolvers[cache_key]

    def _get_field_value(self, record: Dict[str, Any], field_path: str) -> Any:
        """Get a field value from a record, supporting nested fields."""
        parts = field_path.split(".")
        current = record

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        """
        Apply GeoIP lookup to an IP address.

        Args:
            field_name: The name of the field being processed.
            record: The full record (not modified for this mutator).
            value: The IP address to lookup.

        Returns:
            Normalized GeoIP data dictionary or None if lookup fails.
        """
        # Check if maxminddb is available
        if maxminddb is None:
            raise ImportError("maxminddb package is required for GeoIP lookups")

        # Validate input
        if not isinstance(value, str):
            return None

        # Validate IP address
        try:
            ipaddress.ip_address(value)
        except ValueError:
            return None

        # Check if we should force lookup
        force_lookup = self.params.get("force", False)

        # Keep track of existing geo data for potential restoration
        existing_geo_data = None
        existing_as_data = None

        # Check if geo data already exists in the record (ECS style)
        if "." in field_name:
            # For nested fields like destination.ip, check destination.geo and destination.as
            parent_path = field_name.rsplit(".", 1)[0]
            parent = self._get_field_value(record, parent_path)
            if isinstance(parent, dict):
                existing_geo_data = parent.get("geo")
                existing_as_data = parent.get("as")
        else:
            # For top-level fields like ip, check top-level geo and as fields (ECS style)
            existing_geo_data = record.get("geo")
            existing_as_data = record.get("as")

        # If not forcing and geo data exists with at least country_iso_code, return existing
        if (
            not force_lookup
            and existing_geo_data
            and isinstance(existing_geo_data, dict)
            and "country_iso_code" in existing_geo_data
        ):
            result = {}
            if existing_geo_data:
                result["geo"] = existing_geo_data
            if existing_as_data:
                result["as"] = existing_as_data
            return result if result else None

        # Check if caching is disabled
        use_cache = self.params.get("cache", True)
        cache_ttl = self.params.get("cache_ttl", 86400)  # 24 hours default

        # Get cache manager
        cache_manager = self.get_cache_manager() if use_cache else None

        # Try cache first
        if cache_manager:
            cache_key = f"geo:{value}"
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Get GeoIP resolver and perform lookup
        try:
            # Build config only if we have explicit parameters
            # Otherwise pass None to let GeoIPResolver read environment variables
            geo_config = None
            if self.params.get("db_path"):
                geo_config = {"db_path": self.params["db_path"]}

            geo_resolver = self.get_geo_resolver(geo_config)

            # Perform lookup
            raw_data = geo_resolver.lookup(value)

            # Normalize the result
            if raw_data and geo_resolver.db_type:
                normalized = GeoIPNormalizer.normalize(raw_data, geo_resolver.db_type, geo_resolver.mmdb_type)
            else:
                normalized = None
        except Exception:
            # Geo lookup failed (e.g., no database configured)
            normalized = None

        # Cache the result
        if cache_manager and use_cache:
            cache_manager.set(cache_key, normalized, ttl=cache_ttl)

        # Handle force parameter logic
        if force_lookup:
            # When force=true, we always try a fresh lookup
            # If lookup succeeded, return the new data
            # If lookup failed, return None (don't fall back to existing data)
            return normalized
        else:
            # When force=false, prefer existing data if available
            if normalized is None and (existing_geo_data or existing_as_data):
                # Lookup failed but we have existing data - return it
                result = {}
                if existing_geo_data:
                    result["geo"] = existing_geo_data
                if existing_as_data:
                    result["as"] = existing_as_data
                return result
            else:
                # Either lookup succeeded or no existing data
                return normalized
