import pytest
from django.db import IntegrityError
from django.utils import timezone

from nazara.shared.domain.dtos.signal_data import CustomerCaseData
from nazara.shared.domain.value_objects.types import ProcessingResult
from nazara.signals.domain.models import CustomerCase, PriorityChoices


@pytest.mark.django_db
def test_from_data_should_create_and_update_case(create_customer_case):
    source_id = f"test_case_{timezone.now().timestamp()}"
    dto = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        source_url="https://app.intercom.com/conversation/123",
        customer_id="cust_001",
        customer_email="customer@example.com",
        customer_name="Test Customer",
        title="Integration Test Case",
        description="Testing create/update for customer case",
        status="open",
        severity="high",
        priority=1,
        started_at=timezone.now(),
        tags=("test", "integration"),
        metadata={"symptom1": "value1", "symptom2": "value2"},
    )

    result1 = create_customer_case.from_data(dto)
    assert result1 == ProcessingResult.CREATED

    dto2 = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        source_url="https://app.intercom.com/conversation/123",
        customer_id="cust_001",
        customer_email="customer@example.com",
        customer_name="Test Customer",
        title="Integration Test Case",
        description="Testing create/update for customer case",
        status="resolved",
        severity="high",
        priority=2,
        started_at=timezone.now(),
        tags=("test", "integration"),
        metadata={"symptom1": "value1", "symptom2": "value2"},
    )
    result2 = create_customer_case.from_data(dto2)
    assert result2 == ProcessingResult.UPDATED


@pytest.mark.django_db
def test_from_data_should_skip_duplicate_content(create_customer_case):
    source_id = f"dedup_test_{timezone.now().timestamp()}"
    dto = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        customer_id="cust_dedup",
        title="Dedup Test Case",
        description="Testing deduplication",
        status="open",
        severity="medium",
        priority=2,
    )

    result1 = create_customer_case.from_data(dto)
    result2 = create_customer_case.from_data(dto)
    result3 = create_customer_case.from_data(dto)

    assert result1 == ProcessingResult.CREATED
    assert result2 == ProcessingResult.SKIPPED
    assert result3 == ProcessingResult.SKIPPED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "priority_input,expected_priority",
    [
        (0, PriorityChoices.URGENT),
        (1, PriorityChoices.HIGH),
        (2, PriorityChoices.NORMAL),
        (3, PriorityChoices.LOW),
        ("urgent", PriorityChoices.URGENT),
        ("high", PriorityChoices.HIGH),
        ("normal", PriorityChoices.NORMAL),
        ("low", PriorityChoices.LOW),
    ],
)
def test_from_data_should_map_priority_correctly(
    create_customer_case, customer_case_repo, priority_input, expected_priority
):
    source_id = f"priority_test_{priority_input}_{timezone.now().timestamp()}"
    dto = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        customer_id="cust_priority",
        title=f"Priority Test {priority_input}",
        description="Testing priority mapping",
        status="open",
        priority=priority_input if isinstance(priority_input, int) else 2,
    )

    if isinstance(priority_input, str):
        priority_map = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        dto = CustomerCaseData(
            source_system="intercom",
            source_identifier=source_id,
            customer_id="cust_priority",
            title=f"Priority Test {priority_input}",
            description="Testing priority mapping",
            status="open",
            priority=priority_map[priority_input],
        )

    create_customer_case.from_data(dto)

    case = customer_case_repo.get_by_source("intercom", source_id)
    assert case is not None
    assert case.priority == expected_priority


@pytest.mark.django_db
def test_from_data_should_persist_all_fields(create_customer_case, customer_case_repo):
    source_id = f"full_case_{timezone.now().timestamp()}"
    now = timezone.now()
    dto = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        source_url="https://app.intercom.com/conversation/full",
        customer_id="cust_full",
        customer_email="full@example.com",
        customer_name="Full Customer",
        title="Complete Customer Case",
        description="Case with all fields populated",
        status="open",
        severity="critical",
        priority=0,
        started_at=now,
        ended_at=None,
        tags=("billing", "urgent", "enterprise"),
        metadata={"issue": "Cannot login", "error_code": "500"},
        raw_payload={"original": "data"},
        conversation=(
            {"role": "customer", "content": "Help!", "timestamp": None, "author_name": None},
        ),
    )

    result = create_customer_case.from_data(dto)
    assert result == ProcessingResult.CREATED

    case = customer_case_repo.get_by_source("intercom", source_id)

    assert case is not None
    assert case.customer_id == "cust_full"
    assert case.customer_email == "full@example.com"
    assert case.customer_name == "Full Customer"
    assert case.title == "Complete Customer Case"
    assert case.status == "open"
    assert case.severity == "critical"
    assert case.priority == PriorityChoices.URGENT
    assert set(case.tags) == {"billing", "urgent", "enterprise"}
    assert case.metadata.get("issue") == "Cannot login"
    assert case.raw_data == {"original": "data"}
    assert len(case.conversation) == 1
    assert case.conversation[0]["role"] == "customer"


@pytest.mark.django_db
def test_from_data_should_update_priority(create_customer_case, customer_case_repo):
    source_id = f"update_priority_{timezone.now().timestamp()}"
    dto1 = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        customer_id="cust_update",
        title="Priority Update Test",
        description="Testing priority updates",
        status="open",
        priority=3,
    )

    create_customer_case.from_data(dto1)

    dto2 = CustomerCaseData(
        source_system="intercom",
        source_identifier=source_id,
        customer_id="cust_update",
        title="Priority Update Test",
        description="Testing priority updates",
        status="resolved",
        priority=0,
    )
    create_customer_case.from_data(dto2)

    case = customer_case_repo.get_by_source("intercom", source_id)

    assert case is not None
    assert case.priority == PriorityChoices.URGENT
    assert case.status == "resolved"


@pytest.mark.django_db
def test_get_by_source_should_return_none_when_not_found(customer_case_repo):
    result = customer_case_repo.get_by_source("nonexistent", "notfound")
    assert result is None


@pytest.mark.django_db
def test_save_should_create_new_case(customer_case_repo):
    source_id = f"save_new_{timezone.now().timestamp()}"
    case = CustomerCase.create(
        source_system="test_system",
        source_identifier=source_id,
        customer_id="cust_new",
        title="New Case via Save",
        description="Testing save create",
        status="open",
        priority=PriorityChoices.NORMAL,
    )

    saved_case, was_saved = customer_case_repo.save(case)

    assert was_saved is True
    assert saved_case.source_system == "test_system"
    assert saved_case.source_identifier == source_id
    assert saved_case.customer_id == "cust_new"
    assert saved_case.priority == PriorityChoices.NORMAL
    assert saved_case.content_hash is not None


@pytest.mark.django_db
def test_save_should_update_existing_case(customer_case_repo):
    source_id = f"save_update_{timezone.now().timestamp()}"
    case = CustomerCase.create(
        source_system="test_system",
        source_identifier=source_id,
        customer_id="cust_update",
        title="Original Title",
        description="Original description",
        status="open",
        priority=PriorityChoices.LOW,
    )
    case, _ = customer_case_repo.save(case)

    case.apply_changes(
        title="Updated Title",
        description="Updated description",
        status="resolved",
        priority=PriorityChoices.URGENT,
    )
    case2, was_saved = customer_case_repo.save(case)

    assert was_saved is True
    assert case2.id == case.id
    assert case2.title == "Updated Title"
    assert case2.status == "resolved"
    assert case2.priority == PriorityChoices.URGENT


@pytest.mark.django_db
def test_save_should_skip_unchanged_case(customer_case_repo):
    source_id = f"save_unchanged_{timezone.now().timestamp()}"
    case = CustomerCase.create(
        source_system="test_system",
        source_identifier=source_id,
        customer_id="cust_unchanged",
        title="Unchanged Case",
        description="Will not change",
        status="open",
        priority=PriorityChoices.NORMAL,
    )
    case, _ = customer_case_repo.save(case)

    case2, was_saved = customer_case_repo.save(case)

    assert was_saved is False
    assert case2.id == case.id


@pytest.mark.django_db
def test_objects_create_should_enforce_unique_constraint(customer_case_repo):
    source_id = f"unique_test_{timezone.now().timestamp()}"

    CustomerCase.objects.create(
        source_system="test_system",
        source_identifier=source_id,
        customer_id="cust_1",
        title="First Case",
    )

    with pytest.raises(IntegrityError):
        CustomerCase.objects.create(
            source_system="test_system",
            source_identifier=source_id,
            customer_id="cust_2",
            title="Duplicate Case",
        )
