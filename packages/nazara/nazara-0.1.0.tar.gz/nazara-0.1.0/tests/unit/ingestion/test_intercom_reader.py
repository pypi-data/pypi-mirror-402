from datetime import UTC, datetime

import pytest

from nazara.ingestion.infrastructure.readers.intercom_reader import IntercomReader


@pytest.fixture
def reader():
    return IntercomReader()


@pytest.fixture
def minimal_conversation():
    return {
        "id": "conv_123",
        "type": "conversation",
        "state": "open",
        "source": {
            "subject": "Issue with my subscription",
            "body": "I can't access my account after renewal.",
            "author": {
                "id": "author_123",
                "email": "customer@example.com",
                "name": "John Doe",
            },
        },
        "contacts": {
            "contacts": [
                {
                    "id": "contact_456",
                    "external_id": "cust_789",
                }
            ]
        },
        "created_at": 1704067200,
        "updated_at": 1704153600,
    }


def test_get_source_system_should_return_intercom(reader):
    assert reader.get_source_system() == "intercom"


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"type": "conversation", "id": "123"}, True),
        ({"id": "123", "state": "open"}, True),
        ({}, False),
        ({"random_field": "value"}, False),
        (None, False),
    ],
)
def test_validate_payload(reader, payload, expected):
    assert reader.validate_payload(payload) is expected


def test_parse_payload_should_extract_source_system(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.source_system == "intercom"


def test_parse_payload_should_extract_source_identifier(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.source_identifier == "conv_123"


def test_parse_payload_should_extract_title_from_subject(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.title == "Issue with my subscription"


def test_parse_payload_should_extract_description_from_body(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.description == "I can't access my account after renewal."


def test_parse_payload_should_use_external_id_as_customer_id(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.customer_id == "cust_789"


def test_parse_payload_should_extract_customer_email(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.customer_email == "customer@example.com"


def test_parse_payload_should_extract_customer_name(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.customer_name == "John Doe"


def test_parse_payload_should_parse_timestamps(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.started_at == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)


def test_parse_payload_should_preserve_raw_payload(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert result.raw_payload == minimal_conversation


@pytest.mark.parametrize(
    "intercom_state,expected_status",
    [
        ("open", "open"),
        ("closed", "resolved"),
        ("snoozed", "monitoring"),
        ("OPEN", "open"),
        ("Closed", "resolved"),
        ("unknown", "open"),
    ],
)
def test_parse_payload_should_map_status_correctly(reader, intercom_state, expected_status):
    payload = {
        "id": "test",
        "state": intercom_state,
        "source": {"body": "Test"},
    }
    result = reader.parse_payload(payload)
    assert result.status == expected_status


@pytest.mark.parametrize(
    "intercom_priority,expected_priority",
    [
        ("priority", 0),
        (True, 0),
        ("not_priority", 2),
        (False, 2),
        (None, 2),
    ],
)
def test_parse_payload_should_map_priority_correctly(reader, intercom_priority, expected_priority):
    payload = {
        "id": "test",
        "state": "open",
        "priority": intercom_priority,
        "source": {"body": "Test"},
    }
    result = reader.parse_payload(payload)
    assert result.priority == expected_priority


def test_parse_payload_should_fallback_to_contact_id_when_no_external_id(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "contacts": {
            "contacts": [
                {
                    "id": "contact_123",
                }
            ]
        },
        "source": {
            "author": {
                "email": "test@example.com",
            }
        },
    }
    result = reader.parse_payload(payload)
    assert result.customer_id == "intercom:contact_123"
    assert result.customer_email == "test@example.com"


def test_parse_payload_should_fallback_to_source_author_when_no_contacts(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "contacts": {"contacts": []},
        "source": {
            "author": {
                "id": "author_456",
                "email": "author@example.com",
                "name": "Author Name",
            }
        },
    }
    result = reader.parse_payload(payload)
    assert result.customer_id == "intercom:author_456"
    assert result.customer_email == "author@example.com"
    assert result.customer_name == "Author Name"


def test_parse_payload_should_return_unknown_when_no_customer_info(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "contacts": {"contacts": []},
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert result.customer_id == "unknown"


def test_parse_payload_should_use_subject_as_title(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {
            "subject": "Help with billing",
            "body": "Detailed description...",
        },
    }
    result = reader.parse_payload(payload)
    assert result.title == "Help with billing"


def test_parse_payload_should_use_body_first_line_as_title_when_no_subject(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {
            "body": "First line as title\nSecond line with more details",
        },
    }
    result = reader.parse_payload(payload)
    assert result.title == "First line as title"


def test_parse_payload_should_strip_html_tags_from_title(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {
            "body": "<p>Title with <b>bold</b> text</p>",
        },
    }
    result = reader.parse_payload(payload)
    assert result.title == "Title with bold text"


def test_parse_payload_should_truncate_long_titles(reader):
    long_title = "A" * 200
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {"body": long_title},
    }
    result = reader.parse_payload(payload)
    assert len(result.title) == 100
    assert result.title.endswith("...")


def test_parse_payload_should_use_default_title_when_empty(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {"body": ""},
    }
    result = reader.parse_payload(payload)
    assert result.title == "Untitled conversation"


def test_parse_payload_should_include_intercom_source_tag(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert "intercom" in result.tags


def test_parse_payload_should_include_intercom_tags(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "tags": {
            "tags": [
                {"name": "billing"},
                {"name": "urgent"},
            ]
        },
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert "billing" in result.tags
    assert "urgent" in result.tags


def test_parse_payload_should_include_priority_urgent_tag(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "priority": "priority",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert "priority:urgent" in result.tags


def test_parse_payload_should_include_priority_normal_tag(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "priority": "not_priority",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert "priority:normal" in result.tags


def test_parse_payload_should_extract_metadata_from_custom_attributes(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "custom_attributes": {
            "plan": "enterprise",
            "region": "eu-west-1",
        },
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert result.metadata["plan"] == "enterprise"
    assert result.metadata["region"] == "eu-west-1"


def test_parse_payload_should_return_empty_metadata_without_custom_attributes(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert result.metadata == {}


def test_parse_payload_should_build_source_url_with_workspace_id(reader):
    payload = {
        "id": "conv_123",
        "workspace_id": "ws_456",
        "state": "open",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert (
        result.source_url == "https://app.intercom.com/a/inbox/ws_456/inbox/conversation/conv_123"
    )


def test_parse_payload_should_build_source_url_without_workspace_id(reader):
    payload = {
        "id": "conv_123",
        "state": "open",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert result.source_url == "https://app.intercom.com/a/inbox/inbox/conversation/conv_123"


def test_parse_payload_should_extract_ended_at_for_closed_conversation(reader):
    payload = {
        "id": "conv_1",
        "state": "closed",
        "statistics": {
            "last_close_at": 1704240000,
        },
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert result.ended_at == datetime(2024, 1, 3, 0, 0, 0, tzinfo=UTC)


def test_parse_payload_should_return_none_ended_at_for_open_conversation(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {},
    }
    result = reader.parse_payload(payload)
    assert result.ended_at is None


@pytest.mark.parametrize(
    "created_at,expected",
    [
        (1704067200, datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
        ("2024-01-01T00:00:00Z", datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)),
        (None, None),
    ],
)
def test_parse_payload_timestamp_handling(reader, created_at, expected):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {},
    }
    if created_at is not None:
        payload["created_at"] = created_at
    result = reader.parse_payload(payload)
    assert result.started_at == expected


def test_parse_payload_should_include_conversation_field(reader, minimal_conversation):
    result = reader.parse_payload(minimal_conversation)
    assert isinstance(result.conversation, tuple)


def test_parse_payload_should_extract_conversation_from_source(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "created_at": 1704067200,
        "source": {
            "body": "Initial customer message",
            "author": {"name": "Customer"},
        },
    }
    result = reader.parse_payload(payload)
    assert len(result.conversation) == 1
    assert result.conversation[0]["role"] == "customer"
    assert result.conversation[0]["content"] == "Initial customer message"


def test_parse_payload_should_extract_conversation_parts(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "created_at": 1704067200,
        "source": {
            "body": "Help please",
            "author": {"name": "Customer"},
        },
        "conversation_parts": {
            "conversation_parts": [
                {
                    "body": "How can I help?",
                    "created_at": 1704067300,
                    "author": {"type": "admin", "name": "Agent"},
                },
                {
                    "body": "Thanks!",
                    "created_at": 1704067400,
                    "author": {"type": "user", "name": "Customer"},
                },
            ]
        },
    }
    result = reader.parse_payload(payload)
    assert len(result.conversation) == 3
    assert result.conversation[0]["role"] == "customer"
    assert result.conversation[1]["role"] == "agent"
    assert result.conversation[2]["role"] == "customer"


def test_parse_payload_should_map_bot_to_ai_agent(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "source": {"body": "Hi"},
        "conversation_parts": {
            "conversation_parts": [
                {
                    "body": "I'm Fin, how can I help?",
                    "author": {"type": "bot", "name": "Fin"},
                },
            ]
        },
    }
    result = reader.parse_payload(payload)
    assert result.conversation[1]["role"] == "ai_agent"
    assert result.conversation[1]["author_name"] == "Fin"


def test_parse_payload_should_fallback_name_to_email_prefix(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "contacts": {"contacts": []},
        "source": {
            "author": {
                "id": "author_1",
                "email": "john.doe@example.com",
            }
        },
    }
    result = reader.parse_payload(payload)
    assert result.customer_name == "john.doe"


def test_parse_payload_should_get_email_from_source_author_when_contacts_have_id(reader):
    payload = {
        "id": "conv_1",
        "state": "open",
        "contacts": {
            "contacts": [
                {
                    "id": "contact_123",
                    "external_id": "ws_user_456",
                }
            ]
        },
        "source": {
            "author": {
                "email": "real.email@example.com",
                "name": "Real Name",
            }
        },
    }
    result = reader.parse_payload(payload)
    assert result.customer_id == "ws_user_456"
    assert result.customer_email == "real.email@example.com"
    assert result.customer_name == "Real Name"
