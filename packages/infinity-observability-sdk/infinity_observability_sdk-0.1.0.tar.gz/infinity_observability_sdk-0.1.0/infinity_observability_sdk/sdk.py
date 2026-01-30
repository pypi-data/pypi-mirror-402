import os
from contextlib import contextmanager
from dataclasses import dataclass

import logfire
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


@dataclass
class ObservabilityConfig:
    business_unit_name: str
    service_name: str
    instrument_pydantic_ai: bool = True
    instrument_httpx: bool = True


_config: ObservabilityConfig | None = None


@contextmanager
def agent_context(
    agent_employee_equivalent: str,
    hourly_rate: float,
    agent_name: str,
    task_description: str,
    task_instance_identifier: str,
    approximate_person_hours: float,
    **metadata,
):
    global _config

    if _config is None:
        raise Exception(
            "It looks like the infinity constellation monitoring SDK is not yet configured. Please run configure_observability before adding agent_context"
        )

    attributes = {
        "infinity_observability_sdk.agent_employee_equivalent": agent_employee_equivalent,
        "infinity_observability_sdk.hourly_rate": hourly_rate,
        "infinity_observability_sdk.business_unit_name": _config.business_unit_name,
        "infinity_observability_sdk.service_name": _config.service_name,
        "infinity_observability_sdk.agent_name": agent_name,
        "infinity_observability_sdk.task_description": task_description,
        "infinity_observability_sdk.task_instance_identifier": task_instance_identifier,
        "infinity_observability_sdk.approximate_person_hours": approximate_person_hours,
        "infinity_observability_sdk.ai_wattage": approximate_person_hours * hourly_rate,
        "infinity_observability_sdk.is_tracked_agent": True,
        "infinity_observability_sdk.version": "0.1",
        **metadata,
    }

    baggage = {
        "infinity_observability_sdk.baggage.business_unit_name": _config.business_unit_name,
        "infinity_observability_sdk.baggage.service_name": _config.service_name,
        "infinity_observability_sdk.baggage.agent_name": agent_name,
        "infinity_observability_sdk.baggage.is_tracked_agent": "true",
    }

    with (
        logfire.set_baggage(**baggage),
        logfire.span("agent_context", **attributes) as span,
    ):
        yield span


def configure_observability(config: ObservabilityConfig) -> None:
    global _config

    endpoint = os.environ.get("INFINITY_OBSERVABILITY_ENDPOINT")
    api_key = os.environ.get("INFINITY_OBSERVABILITY_API_KEY")

    if not endpoint:
        raise RuntimeError(
            "INFINITY_OBSERVABILITY_ENDPOINT environment variable is required. "
            "Set it to the observability collector endpoint "
        )

    if not api_key:
        raise RuntimeError(
            "INFINITY_OBSERVABILITY_API_KEY environment variable is required. "
            "Set it to your observability API key."
        )

    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{endpoint}/v1/traces",
        headers={"X-Api-Key": api_key},
    )
    span_processor = BatchSpanProcessor(otlp_exporter)

    provider = trace.get_tracer_provider()

    if isinstance(provider, TracerProvider):
        provider.add_span_processor(span_processor)
    else:
        logfire.configure(
            send_to_logfire=False,
            service_name=config.business_unit_name + "." + config.service_name,
            additional_span_processors=[span_processor],
        )

    if config.instrument_httpx:
        logfire.instrument_httpx(capture_all=True)

    if config.instrument_pydantic_ai:
        logfire.instrument_pydantic_ai()

    _config = config

    print(
        "Successfully initialized Infinity Monitoring. OTLP traffic is being forwarded to:",
        endpoint,
    )
