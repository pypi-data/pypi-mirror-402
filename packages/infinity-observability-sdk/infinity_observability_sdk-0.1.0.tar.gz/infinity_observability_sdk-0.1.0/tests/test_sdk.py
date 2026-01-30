from unittest.mock import MagicMock, patch

import pytest

from infinity_observability_sdk import (
    ObservabilityConfig,
    agent_context,
    configure_observability,
)


class TestObservabilityConfig:
    def test_creates_config_with_required_fields(self):
        config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )
        assert config.business_unit_name == "test_bu"
        assert config.service_name == "test_service"
        assert config.instrument_pydantic_ai is True
        assert config.instrument_httpx is True

    def test_creates_config_with_custom_instrumentation(self):
        config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
            instrument_pydantic_ai=False,
            instrument_httpx=False,
        )
        assert config.instrument_pydantic_ai is False
        assert config.instrument_httpx is False


class TestConfigureObservability:
    def test_raises_when_endpoint_not_set(self, monkeypatch):
        monkeypatch.delenv("INFINITY_OBSERVABILITY_ENDPOINT", raising=False)
        monkeypatch.delenv("INFINITY_OBSERVABILITY_API_KEY", raising=False)

        config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        with pytest.raises(RuntimeError, match="INFINITY_OBSERVABILITY_ENDPOINT"):
            configure_observability(config)

    def test_raises_when_api_key_not_set(self, monkeypatch):
        monkeypatch.setenv("INFINITY_OBSERVABILITY_ENDPOINT", "https://example.com")
        monkeypatch.delenv("INFINITY_OBSERVABILITY_API_KEY", raising=False)

        config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        with pytest.raises(RuntimeError, match="API_KEY"):
            configure_observability(config)

    @patch("infinity_observability_sdk.sdk.logfire")
    @patch("infinity_observability_sdk.sdk.trace")
    @patch("infinity_observability_sdk.sdk.BatchSpanProcessor")
    @patch("infinity_observability_sdk.sdk.OTLPSpanExporter")
    def test_configures_logfire_when_not_already_configured(
        self,
        mock_exporter,
        mock_processor,
        mock_trace,
        mock_logfire,
        monkeypatch,
    ):
        monkeypatch.setenv("INFINITY_OBSERVABILITY_ENDPOINT", "https://example.com")
        monkeypatch.setenv("INFINITY_OBSERVABILITY_API_KEY", "test-key")

        # Simulate logfire not configured (returns non-TracerProvider)
        mock_trace.get_tracer_provider.return_value = MagicMock()

        config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        configure_observability(config)

        mock_logfire.configure.assert_called_once()
        call_kwargs = mock_logfire.configure.call_args[1]
        assert call_kwargs["send_to_logfire"] is False
        assert call_kwargs["service_name"] == "test_bu.test_service"

    @patch("infinity_observability_sdk.sdk.logfire")
    @patch("infinity_observability_sdk.sdk.trace")
    @patch("infinity_observability_sdk.sdk.BatchSpanProcessor")
    @patch("infinity_observability_sdk.sdk.OTLPSpanExporter")
    @patch("infinity_observability_sdk.sdk.TracerProvider")
    def test_adds_processor_when_already_configured(
        self,
        mock_tracer_provider_class,
        mock_exporter,
        mock_processor,
        mock_trace,
        mock_logfire,
        monkeypatch,
    ):
        monkeypatch.setenv("INFINITY_OBSERVABILITY_ENDPOINT", "https://example.com")
        monkeypatch.setenv("INFINITY_OBSERVABILITY_API_KEY", "test-key")

        # Simulate logfire already configured (returns real TracerProvider instance)
        mock_provider = MagicMock(spec=["add_span_processor"])
        mock_trace.get_tracer_provider.return_value = mock_provider
        mock_tracer_provider_class.return_value = mock_provider
        # Make isinstance check work
        mock_provider.__class__ = mock_tracer_provider_class

        config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        with patch("infinity_observability_sdk.sdk.isinstance", return_value=True):
            configure_observability(config)

        mock_provider.add_span_processor.assert_called_once()
        mock_logfire.configure.assert_not_called()


class TestAgentContext:
    def test_raises_when_not_configured(self):
        import infinity_observability_sdk.sdk as sdk_module

        sdk_module._config = None

        with pytest.raises(Exception, match="not yet configured"):
            with agent_context(
                agent_employee_equivalent="data_engineer",
                hourly_rate=75.0,
                agent_name="test_agent",
                task_description="test task",
                task_instance_identifier="test-123",
                approximate_person_hours=1.0,
            ):
                pass

    @patch("infinity_observability_sdk.sdk.logfire")
    def test_creates_span_with_correct_attributes(self, mock_logfire):
        import infinity_observability_sdk.sdk as sdk_module

        sdk_module._config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        mock_span = MagicMock()
        mock_logfire.span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_logfire.span.return_value.__exit__ = MagicMock(return_value=False)
        mock_logfire.set_baggage.return_value.__enter__ = MagicMock()
        mock_logfire.set_baggage.return_value.__exit__ = MagicMock(return_value=False)

        with agent_context(
            agent_employee_equivalent="data_engineer",
            hourly_rate=75.0,
            agent_name="test_agent",
            task_description="test task",
            task_instance_identifier="test-123",
            approximate_person_hours=2.0,
        ) as span:
            assert span == mock_span

        # Check span was created with correct attributes
        mock_logfire.span.assert_called_once()
        call_args = mock_logfire.span.call_args
        assert call_args[0][0] == "agent_context"

        attrs = call_args[1]
        assert (
            attrs["infinity_observability_sdk.agent_employee_equivalent"]
            == "data_engineer"
        )
        assert attrs["infinity_observability_sdk.hourly_rate"] == 75.0
        assert attrs["infinity_observability_sdk.business_unit_name"] == "test_bu"
        assert attrs["infinity_observability_sdk.service_name"] == "test_service"
        assert attrs["infinity_observability_sdk.agent_name"] == "test_agent"
        assert attrs["infinity_observability_sdk.approximate_person_hours"] == 2.0
        assert attrs["infinity_observability_sdk.ai_wattage"] == 150.0  # 2.0 * 75.0
        assert attrs["infinity_observability_sdk.is_tracked_agent"] is True

    @patch("infinity_observability_sdk.sdk.logfire")
    def test_sets_baggage_with_correct_keys(self, mock_logfire):
        import infinity_observability_sdk.sdk as sdk_module

        sdk_module._config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        mock_logfire.span.return_value.__enter__ = MagicMock()
        mock_logfire.span.return_value.__exit__ = MagicMock(return_value=False)
        mock_logfire.set_baggage.return_value.__enter__ = MagicMock()
        mock_logfire.set_baggage.return_value.__exit__ = MagicMock(return_value=False)

        with agent_context(
            agent_employee_equivalent="data_engineer",
            hourly_rate=75.0,
            agent_name="test_agent",
            task_description="test task",
            task_instance_identifier="test-123",
            approximate_person_hours=1.0,
        ):
            pass

        mock_logfire.set_baggage.assert_called_once()
        baggage_kwargs = mock_logfire.set_baggage.call_args[1]

        assert (
            baggage_kwargs["infinity_observability_sdk.baggage.business_unit_name"]
            == "test_bu"
        )
        assert (
            baggage_kwargs["infinity_observability_sdk.baggage.service_name"]
            == "test_service"
        )
        assert (
            baggage_kwargs["infinity_observability_sdk.baggage.agent_name"]
            == "test_agent"
        )
        assert (
            baggage_kwargs["infinity_observability_sdk.baggage.is_tracked_agent"]
            == "true"
        )

    @patch("infinity_observability_sdk.sdk.logfire")
    def test_passes_extra_metadata_to_span(self, mock_logfire):
        import infinity_observability_sdk.sdk as sdk_module

        sdk_module._config = ObservabilityConfig(
            business_unit_name="test_bu",
            service_name="test_service",
        )

        mock_logfire.span.return_value.__enter__ = MagicMock()
        mock_logfire.span.return_value.__exit__ = MagicMock(return_value=False)
        mock_logfire.set_baggage.return_value.__enter__ = MagicMock()
        mock_logfire.set_baggage.return_value.__exit__ = MagicMock(return_value=False)

        with agent_context(
            agent_employee_equivalent="data_engineer",
            hourly_rate=75.0,
            agent_name="test_agent",
            task_description="test task",
            task_instance_identifier="test-123",
            approximate_person_hours=1.0,
            custom_field="custom_value",
            another_field=42,
        ):
            pass

        call_kwargs = mock_logfire.span.call_args[1]
        assert call_kwargs["custom_field"] == "custom_value"
        assert call_kwargs["another_field"] == 42
