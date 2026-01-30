"""
Infinity Observability SDK

Provides standardized observability configuration for Infinity services,
including OpenTelemetry tracing via logfire with routing to the central
observability collector.

Required environment variables:
    INFINITY_OBSERVABILITY_ENDPOINT: The OTLP collector endpoint
        (e.g., https://observability.staging.infinityconstellation-labs.com)
    SECRET_INFINITY_OBSERVABILITY_API_KEY: API key for authentication
"""

from .sdk import configure_observability, agent_context, ObservabilityConfig

__all__ = ["configure_observability", "agent_context", "ObservabilityConfig"]
