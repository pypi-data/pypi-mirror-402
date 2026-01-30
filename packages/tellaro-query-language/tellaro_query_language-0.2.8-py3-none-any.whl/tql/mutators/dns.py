"""DNS lookup mutator."""

import ipaddress
import socket
from typing import Any, Dict, List, Optional

try:
    import dns.rdataclass
    import dns.rdatatype
    import dns.resolver

    dns_available = True
except ImportError:
    dns_available = False
    dns = None  # type: ignore

from ..validators import validate_field
from .base import BaseMutator, PerformanceClass, append_to_result


class NSLookupMutator(BaseMutator):
    """
    Enrichment mutator that performs DNS lookups on hostnames or IP addresses.

    Performance Characteristics:
    - In-memory: SLOW - Network I/O for DNS queries (can be mitigated with caching)
    - OpenSearch: SLOW - Network I/O plus post-processing overhead

    This mutator can:
    - Perform forward DNS lookups (hostname to IP)
    - Perform reverse DNS lookups (IP to hostname)
    - Query specific DNS record types
    - Support force lookup to bypass existing data
    - Return ECS-compliant DNS data without modifying the original field value

    Field Storage (ECS-compliant):
    - destination.ip | nslookup → stores at destination.domain
    - source.ip | nslookup → stores at source.domain
    - ip | nslookup → stores at domain
    - Multiple queries store as array of ECS DNS objects

    Parameters:
        servers: List of DNS server IPs to use (optional)
        field: Field name to store results (default: auto-detect from field path)
        append_field: Legacy parameter name for field (deprecated)
        force: Force new lookup even if data exists (default: False)
        save: Save enrichment to record (default: True)
        types: List of DNS record types to query (default: auto-detect)

    Examples:
        # Basic usage with ECS-compliant storage
        destination.ip | nslookup
        source.ip | nslookup

        # Custom DNS servers
        hostname | nslookup(servers=['8.8.8.8'])

        # Custom storage location
        ip | nslookup(field='custom.dns_data')
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(params)
        self.is_enrichment = True
        # DNS lookups are slow due to network I/O
        self.performance_in_memory = PerformanceClass.SLOW
        # Even slower in OpenSearch context due to post-processing overhead
        self.performance_opensearch = PerformanceClass.SLOW

    def apply(self, field_name: str, record: Dict[str, Any], value: Any) -> Any:  # noqa: C901
        # Handle different input types
        if value is None:
            return None

        if isinstance(value, str):
            queries = [value]
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            queries = value
        else:
            return None  # Return None for invalid input types instead of raising

        # Check if we should force lookup
        force_lookup = self.params.get("force", False)
        save_enrichment = self.params.get("save", True)

        # Check if DNS data already exists in the record
        # Determine where to store the enrichment data
        # Priority: field parameter > append_field parameter > default location

        # Check for explicit field parameter first
        if "field" in self.params:
            append_field = self.params["field"]
        elif "append_field" in self.params:
            # Legacy parameter support
            append_field = self.params["append_field"]
        else:
            # Default behavior: use 'domain' as the field name
            # If field is like destination.ip, it should be destination.domain
            # If field is just ip, it should be domain
            if "." in field_name:
                # Nested field like destination.ip
                parent_path = field_name.rsplit(".", 1)[0]
                append_field = parent_path + ".domain"
            else:
                # Top-level field
                append_field = "domain"
        existing_dns_data = None

        # Check for existing data at the append field location
        parts = append_field.split(".")
        current: Optional[Dict[str, Any]] = record
        for part in parts[:-1]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                current = None
                break

        if current and isinstance(current, dict) and parts[-1] in current:
            existing_dns_data = current[parts[-1]]

        # If not forcing and DNS data exists, return it
        if not force_lookup and existing_dns_data:
            return existing_dns_data

        # Get custom DNS servers from parameters, if provided.
        servers = self.params.get("servers")
        if servers is not None:
            if not validate_field(servers, [(list, str)]):
                raise ValueError("The 'servers' parameter must be a list of IP address strings.")
            for srv in servers:
                try:
                    ipaddress.ip_address(srv)
                except ValueError:
                    raise ValueError(f"Invalid DNS server address: {srv}")

        # Get requested DNS record types
        requested_types = self.params.get("types", [])

        resolved_results: Dict[str, Any] = {}

        for query_value in queries:
            # Auto-detect if this is an IP address (for reverse lookup)
            is_ip = False
            try:
                ipaddress.ip_address(query_value)
                is_ip = True
            except ValueError:
                pass

            if servers is not None or requested_types:
                # Use dnspython for advanced queries
                if not dns_available:
                    raise ImportError(
                        "dnspython is required for nslookup with custom servers or specific record types."
                    )

                resolver = dns.resolver.Resolver()
                if servers is not None:
                    resolver.nameservers = servers

                records_list = []

                # Determine which record types to query
                if requested_types:
                    # Use explicitly requested types
                    query_types = requested_types
                elif is_ip:
                    # Auto-detect: reverse lookup for IPs
                    query_types = ["PTR"]
                else:
                    # Auto-detect: common forward lookup types
                    query_types = ["A", "AAAA"]

                # Perform queries for each record type
                for record_type in query_types:
                    try:
                        # Handle reverse lookups for PTR records
                        if record_type == "PTR" and is_ip:
                            # Convert IP to reverse DNS format
                            # Use the already imported ipaddress module
                            ip_obj = ipaddress.ip_address(query_value)
                            if isinstance(ip_obj, ipaddress.IPv4Address):
                                # IPv4 reverse format: 4.3.2.1.in-addr.arpa
                                octets = str(ip_obj).split(".")
                                reverse_name = ".".join(reversed(octets)) + ".in-addr.arpa"
                            else:
                                # IPv6 reverse format
                                hex_str = ip_obj.exploded.replace(":", "")
                                reverse_name = ".".join(reversed(hex_str)) + ".ip6.arpa"

                            answer = resolver.resolve(reverse_name, record_type)
                        else:
                            # Regular forward lookup
                            answer = resolver.resolve(query_value, record_type)

                        for rdata in answer:
                            record_dict = {
                                "class": dns.rdataclass.to_text(rdata.rdclass) if hasattr(rdata, "rdclass") else "IN",
                                "data": rdata.to_text().rstrip("."),  # Remove trailing dot from FQDNs
                                "name": str(answer.qname).rstrip(".") if hasattr(answer, "qname") else query_value,
                                "ttl": answer.ttl if hasattr(answer, "ttl") else 0,
                                "type": record_type,
                            }
                            records_list.append(record_dict)
                    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout, Exception):
                        # Continue to next record type if this one fails
                        continue

                # Convert to ECS-compliant structure
                if records_list:
                    resolved_results[query_value] = self._format_dns_ecs(query_value, records_list, query_types)
                else:
                    resolved_results[query_value] = self._format_dns_ecs(query_value, [], query_types)
            else:
                # Fallback to socket for basic lookups
                try:
                    if is_ip:
                        # Reverse lookup
                        hostname, _, _ = socket.gethostbyaddr(query_value)
                        records = [{"class": "IN", "data": hostname, "name": query_value, "ttl": 0, "type": "PTR"}]
                        resolved_results[query_value] = self._format_dns_ecs(query_value, records, ["PTR"])
                    else:
                        # Forward lookup
                        infos = socket.getaddrinfo(query_value, None)
                        ips = list({str(info[4][0]) for info in infos})
                        records = []
                        for ip in ips:
                            # Determine record type based on IP version
                            try:
                                ip_obj = ipaddress.ip_address(ip)
                                record_type = "A" if ip_obj.version == 4 else "AAAA"
                            except ValueError:
                                record_type = "A"  # Default to A record

                            records.append(
                                {"class": "IN", "data": ip, "name": query_value, "ttl": 0, "type": record_type}
                            )
                        resolved_results[query_value] = self._format_dns_ecs(
                            query_value, records, ["A", "AAAA"] if not is_ip else ["PTR"]
                        )
                except Exception:
                    resolved_results[query_value] = self._format_dns_ecs(
                        query_value, [], ["A", "AAAA"] if not is_ip else ["PTR"]
                    )

        # Save enrichment if requested
        if save_enrichment:
            # Always store ECS data directly, never use IP addresses as field names
            if len(queries) == 1 and queries[0] in resolved_results:
                # Single query: store the ECS data directly
                append_to_result(record, append_field, resolved_results[queries[0]])
            elif len(queries) > 1:
                # Multiple queries: store as array of ECS results
                results_array = []
                for query in queries:
                    if query in resolved_results:
                        results_array.append(resolved_results[query])
                append_to_result(record, append_field, results_array)
            else:
                # No results
                append_to_result(record, append_field, None)

        # For enrichment mutators, return data for comparison
        # The full enrichment data is stored via append_to_result above
        # Return value is used for field comparison (e.g., contains 'dns.google')

        if len(queries) == 1 and queries[0] in resolved_results:
            # Single query: return the first answer for comparison
            dns_data = resolved_results[queries[0]]
            answers = dns_data.get("answers", [])
            return answers[0] if answers else value  # Return first answer or original value
        elif len(queries) > 1:
            # Multiple queries: return array of first answers
            first_answers = []
            for query in queries:
                if query in resolved_results:
                    dns_data = resolved_results[query]
                    answers = dns_data.get("answers", [])
                    if answers:
                        first_answers.append(answers[0])
            return first_answers if first_answers else value
        else:
            # No results: return original value
            return value

    def _format_dns_ecs(  # noqa: C901
        self, query_value: str, records: List[Dict[str, Any]], query_types: List[str]
    ) -> Dict[str, Any]:
        """Format DNS results in ECS-compliant structure.

        Args:
            query_value: The original query (hostname or IP)
            records: List of DNS records returned
            query_types: List of DNS record types that were queried

        Returns:
            ECS-compliant DNS data structure
        """
        # Extract answers as simple array of values
        answers = []
        ttls = []
        types = []

        for record in records:
            data = record.get("data", "")
            if data:
                answers.append(data)
                ttls.append(record.get("ttl", 0))
                types.append(record.get("type", ""))

        # Build clean ECS structure
        ecs_data = {
            "question": {"name": query_value, "type": query_types[0] if query_types else "A"},  # Primary query type
            "answers": answers,  # Simple array of answer values
            "response_code": "NOERROR" if records else "NXDOMAIN",
        }

        # Add TTLs if we have them (optional field)
        if ttls:
            ecs_data["ttl"] = ttls

        # Add types if they vary (optional field)
        if types and len(set(types)) > 1:
            ecs_data["types"] = types

        # Extract resolved IPs for ECS standard field
        resolved_ips = []
        for record in records:
            record_type = record.get("type", "")
            data = record.get("data", "")
            if record_type in ["A", "AAAA"] and data:
                resolved_ips.append(data)

        # Add resolved_ip array (ECS standard field)
        if resolved_ips:
            ecs_data["resolved_ip"] = resolved_ips

        return ecs_data
