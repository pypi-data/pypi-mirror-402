"""GeoIP data normalization for TQL.

This module normalizes GeoIP data from different MMDB providers (MaxMind and DB-IP)
into a consistent format for TQL queries.
"""

from typing import Any, Dict, Optional


class GeoIPNormalizer:
    """Normalizes GeoIP data from different MMDB providers to ECS format.

    Follows Elastic Common Schema (ECS) field naming conventions:
    - geo.* fields: https://www.elastic.co/guide/en/ecs/current/ecs-geo.html
    - as.* fields: https://www.elastic.co/guide/en/ecs/current/ecs-as.html
    """

    @staticmethod
    def normalize(  # noqa: C901
        raw_data: Optional[Dict[str, Any]], provider: str, mmdb_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Normalize GeoIP data to ECS-compliant format.

        Args:
            raw_data: Raw data from MMDB lookup
            provider: Either 'maxmind' or 'dbip'
            mmdb_type: Full type identifier (e.g., 'dbip_pro', 'maxmind_lite')

        Returns:
            Normalized data dictionary following ECS conventions
        """
        if not raw_data:
            return None

        normalized = {}

        # Initialize ECS structure
        geo = {}
        as_info = {}

        # MaxMind format (GeoLite2/GeoIP2)
        if provider == "maxmind":
            # geo.country_* fields (ECS)
            if "country" in raw_data:
                geo["country_iso_code"] = raw_data["country"].get("iso_code")
                geo["country_name"] = raw_data["country"].get("names", {}).get("en")

            # geo.city_name (ECS)
            if "city" in raw_data:
                geo["city_name"] = raw_data["city"].get("names", {}).get("en")

            # geo.postal_code (ECS)
            if "postal" in raw_data:
                geo["postal_code"] = raw_data["postal"].get("code")

            # geo.location (ECS)
            if "location" in raw_data:
                location = raw_data["location"]
                if location.get("latitude") is not None and location.get("longitude") is not None:
                    geo["location"] = {"lat": location["latitude"], "lon": location["longitude"]}
                geo["timezone"] = location.get("time_zone")

            # geo.region_* fields (ECS)
            if "subdivisions" in raw_data and raw_data["subdivisions"]:
                # Take the first subdivision (state/province)
                subdivision = raw_data["subdivisions"][0]
                geo["region_name"] = subdivision.get("names", {}).get("en")
                geo["region_iso_code"] = subdivision.get("iso_code")

            # geo.continent_* fields (ECS)
            if "continent" in raw_data:
                geo["continent_code"] = raw_data["continent"].get("code")
                geo["continent_name"] = raw_data["continent"].get("names", {}).get("en")

            # as.* fields (ECS) - from GeoLite2-ASN or merged data
            if "autonomous_system_number" in raw_data:
                as_info["number"] = raw_data["autonomous_system_number"]
            if "autonomous_system_organization" in raw_data:
                as_info["organization"] = {"name": raw_data["autonomous_system_organization"]}

            # Traits (GeoIP2 paid data)
            if "traits" in raw_data:
                traits = raw_data["traits"]
                if traits.get("autonomous_system_number"):
                    as_info["number"] = traits["autonomous_system_number"]
                if traits.get("autonomous_system_organization"):
                    as_info["organization"] = {"name": traits["autonomous_system_organization"]}
                if traits.get("isp"):
                    # ISP is not part of standard ECS, store in organization
                    if "organization" not in as_info:
                        as_info["organization"] = {}
                    as_info["organization"]["isp"] = traits["isp"]

                # Additional non-ECS fields that might be useful
                if traits.get("connection_type"):
                    normalized["connection_type"] = traits["connection_type"]
                if traits.get("user_type"):
                    normalized["user_type"] = traits["user_type"]

        # DB-IP format
        elif provider == "dbip":
            # geo.country_* fields (ECS)
            if "country" in raw_data:
                geo["country_iso_code"] = raw_data["country"].get("iso_code")
                geo["country_name"] = raw_data["country"].get("names", {}).get("en")
                # Store EU status as custom field
                if raw_data["country"].get("is_in_european_union") is not None:
                    normalized["is_eu"] = raw_data["country"]["is_in_european_union"]

            # geo.city_name (ECS)
            if "city" in raw_data:
                geo["city_name"] = raw_data["city"].get("names", {}).get("en")

            # geo.postal_code (ECS)
            if "postal" in raw_data:
                geo["postal_code"] = raw_data["postal"].get("code")

            # geo.location (ECS)
            if "location" in raw_data:
                location = raw_data["location"]
                if location.get("latitude") is not None and location.get("longitude") is not None:
                    geo["location"] = {"lat": location["latitude"], "lon": location["longitude"]}
                geo["timezone"] = location.get("time_zone")
                # Weather code is not part of ECS, store as custom field
                if location.get("weather_code"):
                    normalized["weather_code"] = location["weather_code"]

            # geo.region_* fields (ECS)
            if "subdivisions" in raw_data and raw_data["subdivisions"]:
                # DB-IP can have multiple subdivisions (state, county)
                # First one is usually the primary subdivision (state)
                subdivision = raw_data["subdivisions"][0]
                geo["region_name"] = subdivision.get("names", {}).get("en")
                geo["region_iso_code"] = subdivision.get("iso_code")

                # If there's a second subdivision (county), store it as custom field
                if len(raw_data["subdivisions"]) > 1:
                    county = raw_data["subdivisions"][1]
                    county_name = county.get("names", {}).get("en")
                    if county_name:
                        normalized["county_name"] = county_name

            # geo.continent_* fields (ECS)
            if "continent" in raw_data:
                geo["continent_code"] = raw_data["continent"].get("code")
                geo["continent_name"] = raw_data["continent"].get("names", {}).get("en")

            # as.* fields (ECS) - from dbip-asn-lite or traits in dbip-full
            if "autonomous_system_number" in raw_data:
                as_info["number"] = raw_data["autonomous_system_number"]
            if "autonomous_system_organization" in raw_data:
                as_info["organization"] = {"name": raw_data["autonomous_system_organization"]}

            # Traits (dbip-full data)
            if "traits" in raw_data:
                traits = raw_data["traits"]
                if traits.get("autonomous_system_number"):
                    as_info["number"] = traits["autonomous_system_number"]
                if traits.get("autonomous_system_organization"):
                    as_info["organization"] = {"name": traits["autonomous_system_organization"]}
                if traits.get("isp"):
                    # ISP is not part of standard ECS, store in organization
                    if "organization" not in as_info:
                        as_info["organization"] = {}
                    as_info["organization"]["isp"] = traits["isp"]
                if traits.get("organization"):
                    # Store organization separately if different from AS org
                    if "organization" not in as_info:
                        as_info["organization"] = {}
                    as_info["organization"]["name"] = traits["organization"]

                # Additional non-ECS fields
                if traits.get("connection_type"):
                    normalized["connection_type"] = traits["connection_type"]
                if traits.get("user_type"):
                    normalized["user_type"] = traits["user_type"]

        # Return properly nested structure for TQL usage
        # This allows natural access like geo.country_iso_code in queries
        if geo:
            # Remove None values from geo dict
            geo_clean = {k: v for k, v in geo.items() if v is not None}
            if geo_clean:  # Only add if there's data
                # Add mmdb_type to geo data
                if mmdb_type:
                    geo_clean["mmdb_type"] = mmdb_type
                normalized["geo"] = geo_clean

        if as_info:
            # Remove None values from as_info dict
            as_clean: Dict[str, Any] = {}
            for k, v in as_info.items():
                if v is not None:
                    if k == "organization" and isinstance(v, dict):
                        # Clean organization sub-dict
                        org_clean = {ok: ov for ok, ov in v.items() if ov is not None}
                        if org_clean:
                            as_clean[k] = org_clean
                    else:
                        as_clean[k] = v
            if as_clean:  # Only add if there's data
                # Add mmdb_type to as data
                if mmdb_type:
                    as_clean["mmdb_type"] = mmdb_type
                normalized["as"] = as_clean

        # Remove None values from top level
        result = {k: v for k, v in normalized.items() if v is not None}

        # Return None if result is empty
        return result if result else None

    @staticmethod
    def merge_data(primary: Dict[str, Any], *additional: Dict[str, Any]) -> Dict[str, Any]:
        """Merge data from multiple MMDB files.

        Args:
            primary: Primary data source (usually city data)
            *additional: Additional data sources (ASN, country, etc.)

        Returns:
            Merged dictionary with all available data
        """
        result = primary.copy() if primary else {}

        for data in additional:
            if data:
                # Don't overwrite existing data, only add missing fields
                for key, value in data.items():
                    if key not in result:
                        result[key] = value

        return result
