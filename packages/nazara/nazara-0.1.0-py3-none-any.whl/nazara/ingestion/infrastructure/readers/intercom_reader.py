import asyncio
import re
from datetime import datetime
from typing import Any, ClassVar

import httpx

from nazara.ingestion.infrastructure.readers.base import BaseSignalReader
from nazara.shared.domain.dtos.signal_data import CustomerCaseData
from nazara.shared.domain.value_objects.types import AuthType, IngestionMode, OutputType

# Intercom-specific status mapping
INTERCOM_STATUS_MAP: dict[str, str] = {
    "open": "open",
    "closed": "resolved",
    "snoozed": "monitoring",
}


class IntercomReader(BaseSignalReader[CustomerCaseData]):
    ingestor_type: ClassVar[str] = "intercom_case"
    output_type: ClassVar[OutputType] = OutputType.CUSTOMER_CASE
    display_name: ClassVar[str] = "Intercom"
    description: ClassVar[str] = "Ingest customer cases from Intercom conversations"
    supported_modes: ClassVar[list[IngestionMode]] = [IngestionMode.POLLING]
    supported_auth_types: ClassVar[list[AuthType]] = [AuthType.API_TOKEN]
    filter_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "states": {
                "type": "array",
                "items": {"type": "string", "enum": ["open", "closed", "snoozed"]},
            },
            "page_size": {"type": "integer", "minimum": 1, "maximum": 150, "default": 50},
            "fetch_conversation": {"type": "boolean", "default": False},
            "max_concurrency": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
        },
    }

    BASE_URL: ClassVar[str] = "https://api.intercom.io"
    API_VERSION: ClassVar[str] = "2.11"

    def get_source_system(self) -> str:
        return "intercom"

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        if not super().validate_payload(payload):
            return False
        return payload.get("type") == "conversation" or "id" in payload

    def parse_payload(self, raw_payload: dict[str, Any]) -> CustomerCaseData:
        conv_id = str(raw_payload.get("id", ""))
        source = raw_payload.get("source", {})
        source_author = source.get("author", {})
        contacts = raw_payload.get("contacts", {}).get("contacts", [])

        customer_id, customer_email, customer_name = self._extract_customer(contacts, source_author)
        title = self._extract_title(source)

        state = raw_payload.get("state", "open")
        status = INTERCOM_STATUS_MAP.get(state.lower(), "open")

        priority_val = raw_payload.get("priority")
        priority = 0 if priority_val in ("priority", True) else 2

        started_at = self._parse_timestamp(raw_payload.get("created_at"))
        ended_at = None
        if state == "closed":
            ended_at = self._parse_timestamp(
                self._safe_get(raw_payload, "statistics", "last_close_at")
            )

        workspace_id = raw_payload.get("workspace_id")
        if workspace_id:
            source_url = (
                f"https://app.intercom.com/a/inbox/{workspace_id}/inbox/conversation/{conv_id}"
            )
        else:
            source_url = f"https://app.intercom.com/a/inbox/inbox/conversation/{conv_id}"

        tags = ["intercom"]
        for tag in raw_payload.get("tags", {}).get("tags", []):
            if isinstance(tag, dict) and tag.get("name"):
                tags.append(tag["name"])
        tags.append("priority:urgent" if priority == 0 else "priority:normal")

        metadata = dict(raw_payload.get("custom_attributes", {}))
        conversation = self._extract_conversation(raw_payload)
        body = self._sanitize_string(source.get("body", "")) or ""

        # Extract category from custom attributes (e.g., "Issue Type")
        category = metadata.get("Issue Type")

        return CustomerCaseData(
            source_system=self.get_source_system(),
            source_identifier=conv_id,
            customer_id=customer_id,
            title=title[:500] if title else "Untitled conversation",
            description=body[:5000],
            status=status,
            severity="medium",
            priority=priority,
            category=category,
            customer_email=customer_email,
            customer_name=customer_name,
            source_url=source_url,
            started_at=started_at,
            ended_at=ended_at,
            tags=tuple(tags),
            metadata=metadata,
            conversation=conversation,
            raw_payload=raw_payload,
        )

    def fetch_updates(
        self,
        credentials: str,
        filters: dict[str, Any],
        cursor: str | None,
        since: datetime | None,
    ) -> tuple[list[CustomerCaseData], str | None]:
        headers = {
            "Authorization": f"Bearer {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Intercom-Version": self.API_VERSION,
        }

        page_size = filters.get("page_size", 50)
        fetch_conversation = filters.get("fetch_conversation", False)
        max_concurrency = filters.get("max_concurrency", 10)

        if cursor:
            query_after = int(datetime.fromisoformat(cursor).timestamp())
        elif since:
            query_after = int(since.timestamp())
        else:
            from datetime import UTC

            query_after = int(datetime.now(UTC).timestamp()) - (30 * 24 * 60 * 60)

        query_parts: list[dict[str, Any]] = [
            {"field": "updated_at", "operator": ">", "value": query_after}
        ]
        states = filters.get("states")
        if states:
            query_parts.append({"field": "state", "operator": "IN", "value": states})

        search_body: dict[str, Any] = {
            "query": {"operator": "AND", "value": query_parts},
            "pagination": {"per_page": page_size},
        }

        # Collect all conversations from search (may be partial data)
        conversations: list[dict[str, Any]] = []

        with httpx.Client(timeout=30.0) as client:
            while True:
                response = client.post(
                    f"{self.BASE_URL}/conversations/search",
                    headers=headers,
                    json=search_body,
                )
                response.raise_for_status()
                data = response.json()

                conversations.extend(data.get("conversations", []))

                next_page = data.get("pages", {}).get("next", {}).get("starting_after")
                if next_page:
                    search_body["pagination"]["starting_after"] = next_page
                else:
                    break

        # Fetch full conversation details in parallel if requested
        if fetch_conversation and conversations:
            conversation_ids = [c["id"] for c in conversations]
            full_conversations = asyncio.run(
                self._fetch_conversations_parallel(conversation_ids, headers, max_concurrency)
            )
            # Replace partial data with full data
            conversations = full_conversations

        # Parse all conversations and track max updated_at
        results: list[CustomerCaseData] = []
        max_updated_at: datetime | None = None

        for conv in conversations:
            results.append(self.parse_payload(conv))
            updated_at = self._parse_timestamp(conv.get("updated_at"))
            if updated_at and (max_updated_at is None or updated_at > max_updated_at):
                max_updated_at = updated_at

        new_cursor = max_updated_at.isoformat() if max_updated_at else None
        return results, new_cursor

    async def _fetch_conversations_parallel(
        self,
        conversation_ids: list[str],
        headers: dict[str, str],
        max_concurrency: int,
    ) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async with httpx.AsyncClient(timeout=30.0) as client:

            async def fetch_one(conv_id: str) -> dict[str, Any]:
                async with semaphore:
                    response = await client.get(
                        f"{self.BASE_URL}/conversations/{conv_id}",
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()

            tasks = [fetch_one(conv_id) for conv_id in conversation_ids]
            return list(await asyncio.gather(*tasks))

    def _extract_customer(
        self,
        contacts: list[dict[str, Any]],
        source_author: dict[str, Any],
    ) -> tuple[str, str | None, str]:
        customer_id = "unknown"
        customer_email = None
        customer_name = ""

        if contacts:
            contact = contacts[0]
            if contact.get("external_id"):
                customer_id = contact["external_id"]
            elif contact.get("id"):
                customer_id = f"intercom:{contact['id']}"

        if source_author:
            customer_email = source_author.get("email")
            customer_name = source_author.get("name") or ""
            if customer_id == "unknown" and source_author.get("id"):
                customer_id = f"intercom:{source_author['id']}"

        if not customer_name and customer_email:
            customer_name = customer_email.split("@")[0]

        return customer_id, customer_email, customer_name

    def _extract_title(self, source: dict[str, Any]) -> str:
        subject = source.get("subject")
        if subject:
            return self._sanitize_string(subject) or ""

        body = self._sanitize_string(source.get("body", "")) or ""
        clean_body = re.sub(r"<[^>]+>", "", body)
        first_line = clean_body.split("\n")[0].strip()

        if len(first_line) > 100:
            return first_line[:97] + "..."
        return first_line or "Untitled conversation"

    def _extract_conversation(self, conv: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        thread: list[dict[str, Any]] = []

        source = conv.get("source", {})
        if source.get("body"):
            thread.append(
                {
                    "role": "customer",
                    "content": self._sanitize_string(source.get("body", "")),
                    "timestamp": self._format_ts(conv.get("created_at")),
                    "author_name": source.get("author", {}).get("name"),
                }
            )

        role_map = {"user": "customer", "admin": "agent", "bot": "ai_agent"}
        for part in conv.get("conversation_parts", {}).get("conversation_parts", []):
            if not part.get("body"):
                continue
            author = part.get("author", {})
            thread.append(
                {
                    "role": role_map.get(author.get("type", ""), "system"),
                    "content": self._sanitize_string(part.get("body", "")),
                    "timestamp": self._format_ts(part.get("created_at")),
                    "author_name": author.get("name"),
                }
            )

        return tuple(thread)

    def _format_ts(self, value: Any) -> str | None:
        ts = self._parse_timestamp(value)
        return ts.isoformat() if ts else None
