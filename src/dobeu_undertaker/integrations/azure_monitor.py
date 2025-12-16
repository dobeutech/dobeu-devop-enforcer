"""
Azure Monitor integration for Dobeu Undertaker.

Provides functionality to:
- Send telemetry to Application Insights
- Track custom metrics
- Log events and exceptions
- Create distributed traces
"""

import os
from datetime import datetime, timezone
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from dobeu_undertaker.config.schema import AzureConfig, MonitoringConfig
from dobeu_undertaker.utils.logging import get_logger

logger = get_logger(__name__)


class AzureMonitorClient:
    """
    Client for Azure Monitor / Application Insights integration.

    Handles telemetry collection and export for observability.
    """

    def __init__(
        self,
        azure_config: AzureConfig,
        monitoring_config: MonitoringConfig,
    ) -> None:
        """
        Initialize the Azure Monitor client.

        Args:
            azure_config: Azure configuration
            monitoring_config: Monitoring configuration
        """
        self.azure_config = azure_config
        self.monitoring_config = monitoring_config
        self._tracer: trace.Tracer | None = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize OpenTelemetry with Azure Monitor exporter."""
        if self._initialized:
            return

        connection_string = os.environ.get(
            self.azure_config.connection_string_env_var
        ) or self.azure_config.instrumentation_key

        if not connection_string:
            logger.warning(
                "Azure Monitor connection string not found. "
                "Telemetry will not be exported."
            )
            return

        try:
            # Import Azure Monitor exporter
            from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

            # Create resource with service information
            resource = Resource.create({
                "service.name": "dobeu-undertaker",
                "service.version": "0.1.0",
                "service.namespace": "dobeu-tech",
            })

            # Set up tracer provider
            provider = TracerProvider(resource=resource)

            # Add Azure Monitor exporter
            exporter = AzureMonitorTraceExporter(connection_string=connection_string)
            provider.add_span_processor(BatchSpanProcessor(exporter))

            # Set global tracer provider
            trace.set_tracer_provider(provider)

            self._tracer = trace.get_tracer(__name__)
            self._initialized = True

            logger.info("Azure Monitor telemetry initialized")

        except ImportError:
            logger.warning(
                "azure-monitor-opentelemetry not installed. "
                "Run: pip install azure-monitor-opentelemetry"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure Monitor: {e}")

    def get_tracer(self) -> trace.Tracer:
        """Get the OpenTelemetry tracer."""
        if not self._initialized:
            self.initialize()

        if self._tracer is None:
            # Return a no-op tracer if initialization failed
            return trace.get_tracer(__name__)

        return self._tracer

    def track_scan_started(
        self,
        repo_path: str,
        agents: list[str],
    ) -> trace.Span:
        """
        Track the start of a compliance scan.

        Args:
            repo_path: Repository being scanned
            agents: List of agents being run

        Returns:
            Span for the scan operation
        """
        tracer = self.get_tracer()

        span = tracer.start_span(
            "compliance_scan",
            attributes={
                "repo.path": repo_path,
                "agents.count": len(agents),
                "agents.names": ",".join(agents),
                "scan.start_time": datetime.now(timezone.utc).isoformat(),
            },
        )

        return span

    def track_scan_completed(
        self,
        span: trace.Span,
        results: list[dict[str, Any]],
    ) -> None:
        """
        Track the completion of a compliance scan.

        Args:
            span: The scan span to complete
            results: Scan results from all agents
        """
        total_issues = sum(len(r.get("issues", [])) for r in results)
        critical_count = sum(
            len([i for i in r.get("issues", []) if i.get("severity") == "critical"])
            for r in results
        )
        high_count = sum(
            len([i for i in r.get("issues", []) if i.get("severity") == "high"])
            for r in results
        )

        # Determine overall status
        statuses = [r.get("status", "unknown") for r in results]
        if "failed" in statuses or "error" in statuses:
            overall_status = "failed"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "passed"

        span.set_attributes({
            "scan.end_time": datetime.now(timezone.utc).isoformat(),
            "scan.status": overall_status,
            "scan.total_issues": total_issues,
            "scan.critical_issues": critical_count,
            "scan.high_issues": high_count,
        })

        if overall_status == "failed":
            span.set_status(trace.StatusCode.ERROR, "Compliance scan failed")
        else:
            span.set_status(trace.StatusCode.OK)

        span.end()

    def track_agent_execution(
        self,
        agent_name: str,
        duration_ms: int,
        status: str,
        issue_count: int,
    ) -> None:
        """
        Track execution of a single agent.

        Args:
            agent_name: Name of the agent
            duration_ms: Execution duration in milliseconds
            status: Agent status (passed, failed, etc.)
            issue_count: Number of issues found
        """
        tracer = self.get_tracer()

        with tracer.start_as_current_span(f"agent_{agent_name}") as span:
            span.set_attributes({
                "agent.name": agent_name,
                "agent.duration_ms": duration_ms,
                "agent.status": status,
                "agent.issue_count": issue_count,
            })

            if status in ("failed", "error"):
                span.set_status(trace.StatusCode.ERROR, f"Agent {agent_name} failed")

    def track_custom_metric(
        self,
        name: str,
        value: float,
        dimensions: dict[str, str] | None = None,
    ) -> None:
        """
        Track a custom metric.

        Args:
            name: Metric name
            value: Metric value
            dimensions: Optional dimensions for the metric
        """
        # For custom metrics, we'd typically use the metrics API
        # This is a simplified implementation using spans
        tracer = self.get_tracer()

        with tracer.start_as_current_span(f"metric_{name}") as span:
            span.set_attributes({
                "metric.name": name,
                "metric.value": value,
                **(dimensions or {}),
            })

    def track_exception(
        self,
        exception: Exception,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Track an exception.

        Args:
            exception: The exception to track
            context: Additional context information
        """
        tracer = self.get_tracer()

        with tracer.start_as_current_span("exception") as span:
            span.set_status(trace.StatusCode.ERROR, str(exception))
            span.record_exception(exception)

            if context:
                span.set_attributes({
                    f"context.{k}": str(v) for k, v in context.items()
                })

    def track_event(
        self,
        event_name: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """
        Track a custom event.

        Args:
            event_name: Name of the event
            properties: Event properties
        """
        tracer = self.get_tracer()

        with tracer.start_as_current_span(event_name) as span:
            span.set_attributes({
                "event.name": event_name,
                "event.timestamp": datetime.now(timezone.utc).isoformat(),
                **(properties or {}),
            })


class TelemetryContext:
    """
    Context manager for tracking operations with telemetry.

    Usage:
        async with TelemetryContext(monitor, "operation_name") as ctx:
            # Do work
            ctx.add_attribute("custom.attr", "value")
    """

    def __init__(
        self,
        monitor: AzureMonitorClient,
        operation_name: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.monitor = monitor
        self.operation_name = operation_name
        self.attributes = attributes or {}
        self._span: trace.Span | None = None

    async def __aenter__(self) -> "TelemetryContext":
        tracer = self.monitor.get_tracer()
        self._span = tracer.start_span(self.operation_name, attributes=self.attributes)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._span:
            if exc_val:
                self._span.set_status(trace.StatusCode.ERROR, str(exc_val))
                self._span.record_exception(exc_val)
            else:
                self._span.set_status(trace.StatusCode.OK)
            self._span.end()

    def add_attribute(self, key: str, value: Any) -> None:
        """Add an attribute to the current span."""
        if self._span:
            self._span.set_attribute(key, value)
