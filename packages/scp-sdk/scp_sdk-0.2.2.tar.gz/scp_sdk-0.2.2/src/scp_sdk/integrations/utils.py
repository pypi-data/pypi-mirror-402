"""Common utilities for building integrations."""

from typing import Any, Callable
import time


class FieldMapper:
    """Maps SCP fields to vendor-specific fields.

    Handles translation between the standardized SCP schema and vendor-specific
    data models. Supports direct mapping and basic nesting.

    Example:
        >>> mapping = {
        ...     "vendor_name": "system.name",
        ...     "vendor_tier": "system.classification.tier"
        ... }
        >>> mapper = FieldMapper(mapping)
        >>> result = mapper.map_fields(scp_data)
    """

    def __init__(self, mapping: dict[str, str | list[str]]):
        """Initialize with field mapping configuration.

        Args:
            mapping: Dictionary mapping vendor fields to SCP fields
                    Values can be:
                    - string: dot-notation path to SCP field (e.g. "system.name")
                    - list: multiple SCP fields (combined strategy varies)
        """
        self.mapping = mapping

    def map_fields(self, scp_data: dict[str, Any]) -> dict[str, Any]:
        """Map SCP data to vendor format.

        Args:
            scp_data: SCP system/node data

        Returns:
            Vendor-formatted dictionary
        """
        result = {}

        for vendor_field, scp_field in self.mapping.items():
            if isinstance(scp_field, str):
                # Direct mapping
                if scp_field in scp_data and scp_data[scp_field] is not None:
                    result[vendor_field] = scp_data[scp_field]
            elif isinstance(scp_field, list):
                # Multiple fields - for now, skip (integration-specific)
                pass

        return result

    def extract_value(self, scp_data: dict[str, Any], path: str) -> Any:
        """Extract nested value using dot notation.

        Args:
            scp_data: Source data
            path: Dot-separated path (e.g., "system.tier")

        Returns:
            Value at path, or None if not found
        """
        parts = path.split(".")
        current = scp_data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current


class IDCache:
    """Cache URN to vendor ID mappings.

    Minimizes API calls by caching resolved vendor IDs.
    Essential for performance when syncing large graphs.

    Example:
        >>> cache = IDCache()
        >>> # Get with fetch fallback
        >>> vendor_id = cache.get_or_fetch(
        ...     urn="urn:scp:svc",
        ...     fetch_fn=lambda u: api.lookup(u)
        ... )
    """

    def __init__(self):
        """Initialize empty cache."""
        self._cache: dict[str, str] = {}

    def get(self, urn: str) -> str | None:
        """Get cached vendor ID.

        Args:
            urn: System URN

        Returns:
            Vendor ID if cached, None otherwise
        """
        return self._cache.get(urn)

    def set(self, urn: str, vendor_id: str) -> None:
        """Cache vendor ID.

        Args:
            urn: System URN
            vendor_id: Vendor's system ID
        """
        self._cache[urn] = vendor_id

    def get_or_fetch(
        self, urn: str, fetch_fn: Callable[[str], str | None]
    ) -> str | None:
        """Get cached ID or fetch if not cached.

        Args:
            urn: System URN
            fetch_fn: Function to fetch vendor ID if not cached

        Returns:
            Vendor ID or None if not found
        """
        if urn in self._cache:
            return self._cache[urn]

        vendor_id = fetch_fn(urn)
        if vendor_id:
            self._cache[urn] = vendor_id

        return vendor_id

    def clear(self) -> None:
        """Clear all cached IDs."""
        self._cache.clear()


class BatchProcessor:
    """Process items in batches with rate limiting.

    Utility to handle API rate limits and optimize throughput.
    Groups items into chunks and optionally sleeps between chunks.

    Example:
        >>> processor = BatchProcessor(batch_size=50, delay_seconds=0.5)
        >>> processor.process(items, push_to_api)
    """

    def __init__(self, batch_size: int = 100, delay_seconds: float = 0):
        """Initialize batch processor.

        Args:
            batch_size: Number of items per batch
            delay_seconds: Delay between batches (for rate limiting)
        """
        self.batch_size = batch_size
        self.delay_seconds = delay_seconds

    def process(
        self,
        items: list[Any],
        process_fn: Callable[[list[Any]], None],
    ) -> None:
        """Process items in batches.

        Args:
            items: Items to process
            process_fn: Function that processes a batch
        """
        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            process_fn(batch)

            # Rate limiting
            if self.delay_seconds > 0 and i + self.batch_size < len(items):
                time.sleep(self.delay_seconds)


class CommentBuilder:
    """Build formatted comment/description fields.

    Generates standardized metadata blocks for vendor description fields.
    Useful for ensuring SCP owners and contact info appear in vendor tools.

    Example:
        >>> builder = CommentBuilder()
        >>> description = builder.build(system_data)
        >>> # Result:
        >>> # SCP Metadata:
        >>> # Team: Checkout
        >>> # Domain: Payments
    """

    def __init__(self, template: str | None = None):
        """Initialize with optional template.

        Args:
            template: Format string template (uses Python .format())
        """
        self.template = template or self._default_template()

    def _default_template(self) -> str:
        """Get default template format."""
        return """SCP Metadata:
Team: {team}
Domain: {domain}

Contacts:
{contacts}

Escalation Chain:
{escalation}"""

    def build(self, data: dict[str, Any]) -> str:
        """Build comment using template.

        Args:
            data: System data

        Returns:
            Formatted comment string
        """
        # Prepare contacts
        contacts_list = data.get("contacts", [])
        contacts_str = "\n".join(
            [f"  - {c.get('type')}: {c.get('ref')}" for c in contacts_list]
        )

        # Prepare escalation
        escalation_list = data.get("escalation", [])
        escalation_str = " → ".join(escalation_list) if escalation_list else "N/A"

        format_data = {
            "team": data.get("team", "N/A"),
            "domain": data.get("domain", "N/A"),
            "contacts": contacts_str or "  None",
            "escalation": escalation_str,
        }

        return self.template.format(**format_data)
