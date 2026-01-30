import pytest

from nazara.ingestion.infrastructure.readers.datadog_reader import DatadogReader
from nazara.ingestion.infrastructure.readers.incident_io_reader import IncidentIoReader
from nazara.ingestion.infrastructure.readers.intercom_reader import IntercomReader
from nazara.ingestion.infrastructure.readers.sentry_reader import SentryReader
from nazara.shared.domain.value_objects.types import AuthType, IngestionMode, OutputType


@pytest.mark.parametrize(
    "reader_class,expected_type,expected_output",
    [
        (SentryReader, "sentry_event", OutputType.TECHNICAL_EVENT),
        (DatadogReader, "datadog_event", OutputType.TECHNICAL_EVENT),
        (IncidentIoReader, "incident_io_incident", OutputType.INCIDENT),
        (IntercomReader, "intercom_case", OutputType.CUSTOMER_CASE),
    ],
)
def test_reader_should_have_correct_identity_metadata(reader_class, expected_type, expected_output):
    assert reader_class.ingestor_type == expected_type
    assert reader_class.output_type == expected_output


@pytest.mark.parametrize(
    "reader_class",
    [SentryReader, DatadogReader, IncidentIoReader, IntercomReader],
)
def test_reader_should_have_display_metadata(reader_class):
    assert hasattr(reader_class, "display_name")
    assert hasattr(reader_class, "description")
    assert isinstance(reader_class.display_name, str)
    assert isinstance(reader_class.description, str)
    assert len(reader_class.display_name) > 0
    assert len(reader_class.description) > 0


@pytest.mark.parametrize(
    "reader_class",
    [SentryReader, DatadogReader, IncidentIoReader, IntercomReader],
)
def test_reader_should_have_capability_metadata(reader_class):
    assert hasattr(reader_class, "supported_modes")
    assert hasattr(reader_class, "supported_auth_types")
    assert isinstance(reader_class.supported_modes, list)
    assert isinstance(reader_class.supported_auth_types, list)
    assert len(reader_class.supported_modes) > 0
    assert len(reader_class.supported_auth_types) > 0
    for mode in reader_class.supported_modes:
        assert isinstance(mode, IngestionMode)
    for auth_type in reader_class.supported_auth_types:
        assert isinstance(auth_type, AuthType)


@pytest.mark.parametrize(
    "reader_class",
    [SentryReader, DatadogReader, IncidentIoReader, IntercomReader],
)
def test_reader_should_have_filter_schema(reader_class):
    assert hasattr(reader_class, "filter_schema")
    assert isinstance(reader_class.filter_schema, dict)
    assert "type" in reader_class.filter_schema
    assert reader_class.filter_schema["type"] == "object"


def test_incident_io_reader_should_require_package():
    assert IncidentIoReader.requires_package == "python-incidentio-client"


def test_datadog_reader_should_require_package():
    assert DatadogReader.requires_package == "datadog-api-client"


def test_sentry_reader_should_not_require_package():
    assert SentryReader.requires_package is None


def test_intercom_reader_should_not_require_package():
    assert IntercomReader.requires_package is None


@pytest.mark.parametrize(
    "reader_class",
    [SentryReader, DatadogReader, IncidentIoReader, IntercomReader],
)
def test_reader_should_return_complete_metadata(reader_class):
    metadata = reader_class.get_metadata()

    assert isinstance(metadata, dict)
    assert "ingestor_type" in metadata
    assert "output_type" in metadata
    assert "display_name" in metadata
    assert "description" in metadata
    assert "supported_modes" in metadata
    assert "supported_auth_types" in metadata
    assert "filter_schema" in metadata
    assert metadata["output_type"] == reader_class.output_type.value
    assert all(isinstance(m, str) for m in metadata["supported_modes"])


def test_incident_io_reader_should_support_hybrid_mode():
    assert IngestionMode.HYBRID in IncidentIoReader.supported_modes
    assert IngestionMode.POLLING in IncidentIoReader.supported_modes
    assert IngestionMode.WEBHOOK in IncidentIoReader.supported_modes
