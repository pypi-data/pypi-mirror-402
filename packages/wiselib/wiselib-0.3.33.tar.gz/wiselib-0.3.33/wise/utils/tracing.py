from functools import wraps
from typing import Callable, Any
import re
import logging

from django.conf import settings

# We import QuerySet to detect it, but inside a try/except in case
# this utility is ever moved to a non-Django context.
try:
    from django.db.models import QuerySet
except ImportError:
    QuerySet = None  # type: ignore

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased


class TracingDataFilter:
    """Configuration for filtering sensitive data in OpenTelemetry traces"""

    def __init__(
        self,
        sensitive_patterns: list[str] | None = None,
        sensitive_keys: list[str] | None = None,
        max_string_length: int = 50,
        max_depth: int = 4,
        redaction_text: str = "[REDACTED]",
        log_return_values: bool = True,
    ):
        # Default patterns that are commonly sensitive
        self.sensitive_patterns = sensitive_patterns or [
            r"password",
            r"secret",
            r"private",
            r"token",
            r"key",
            r"nonce",
            r"code",
            r"phrase",
            r"mnemonic",
            r"seed",
            r"credential",
            r"auth",
            r"login",
            r"bearer",
        ]

        # Specific keys that are always sensitive
        self.sensitive_keys = sensitive_keys or []

        # Configuration
        self.max_string_length = max_string_length
        self.max_depth = max_depth
        self.redaction_text = redaction_text
        self.log_return_values = log_return_values

        # Compile patterns for efficiency
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns
        ]

    def is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive information"""
        key_lower = key.lower()

        # Check specific keys first
        if key_lower in [k.lower() for k in self.sensitive_keys]:
            return True

        # Check patterns
        return any(pattern.search(key_lower) for pattern in self._compiled_patterns)

    def sanitize_value(self, value: Any) -> Any:
        """Sanitize sensitive values based on type and length"""
        if isinstance(value, str):
            # Redact based on length
            if len(value) > self.max_string_length:
                return self.redaction_text

        # Note: We don't check dict/list length here,
        # that is handled in safe_serialize_data recursion
        return value

    def safe_serialize_data(self, data: Any, current_depth: int = 0) -> Any:
        """
        Safely serialize data, filtering sensitive information.
        Includes protection against recursion loops and accidental DB queries.
        """
        # 1. Depth Limit Check
        if current_depth >= self.max_depth:
            return "[MAX DEPTH REACHED]"

        # 2. Primitives
        if data is None or isinstance(data, (int, float, bool)):
            return data

        if isinstance(data, str):
            return self.sanitize_value(data)

        # 3. Django QuerySet Protection
        # calling repr() on a QuerySet executes the SQL. We must avoid this.
        if QuerySet and isinstance(data, QuerySet):  # type: ignore
            try:
                model_name = data.model.__name__
            except AttributeError:
                model_name = "Unknown"
            return f"<QuerySet model={model_name}>"

        # 4. Dictionaries
        if isinstance(data, dict):
            safe_dict = {}
            for k, v in data.items():
                str_k = str(k)
                # If the key matches any of the sensitive patterns, REDACT it
                if self.is_sensitive_key(str_k):
                    safe_dict[str_k] = self.redaction_text
                else:
                    safe_dict[str_k] = self.safe_serialize_data(v, current_depth + 1)
            return safe_dict

        # 5. Iterables
        if isinstance(data, (list, tuple, set)):
            return [self.safe_serialize_data(item, current_depth + 1) for item in data]

        # 6. Attempt to Traverse Objects as Dicts
        # This catches Pydantic models, Dataclasses, and standard objects
        if hasattr(data, "__dict__") or hasattr(data, "dict"):
            try:
                # Try Pydantic v1/v2 .dict() or .model_dump() if preferred,
                # otherwise standard vars()
                if hasattr(data, "dict") and callable(data.dict):
                    as_dict = data.dict()
                elif hasattr(data, "model_dump") and callable(data.model_dump):
                    as_dict = data.model_dump()
                else:
                    as_dict = vars(data)

                # RECURSIVELY call self to hit Step 4 (Dictionary filtering)
                return self.safe_serialize_data(as_dict, current_depth)
            except Exception:
                # If conversion fails, fall through to string representation
                pass

        # 7. Fallback
        try:
            string_repr = repr(data)
        except Exception:
            string_repr = "<Unprintable Object>"

        # We sanitize the repr string just in case the repr string is massive.
        return self.sanitize_value(string_repr)


# Global data filter instance
_data_filter = TracingDataFilter()
_filtering_enabled = False  # Default: no filtering (backward compatible)


def configure_tracing_data_filter(
    sensitive_patterns: list[str] | None = None,
    sensitive_keys: list[str] | None = None,
    max_string_length: int = 50,
    max_depth: int = 4,
    redaction_text: str = "[REDACTED]",
    log_return_values: bool = True,
):
    """
    Configure and enable sensitive data filtering in OpenTelemetry traces.
    """
    global _data_filter, _filtering_enabled

    _data_filter = TracingDataFilter(
        sensitive_patterns=sensitive_patterns,
        sensitive_keys=sensitive_keys,
        max_string_length=max_string_length,
        max_depth=max_depth,
        redaction_text=redaction_text,
        log_return_values=log_return_values,
    )
    _filtering_enabled = True


tracing_settings = getattr(settings.ENV, "tracing", None)

resource = Resource(
    attributes={
        SERVICE_NAME: getattr(tracing_settings, "service_name", None)
        or settings.ENV.service_name
    }
)
provider = TracerProvider(
    resource=resource,
    sampler=TraceIdRatioBased(getattr(tracing_settings, "sample_ratio", 0.1)),
)
if getattr(tracing_settings, "enabled", False):
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=getattr(tracing_settings, "url"))
    )
    provider.add_span_processor(processor)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


def with_trace(
    name: str,
    no_input_args: bool = False,
    no_return_value: bool = False,
    filter_sensitive: bool | None = None,
) -> Callable:
    """
    Decorator to add OpenTelemetry tracing to functions.

    Args:
        name: Name for the span in traces
        no_input_args: If True, don't log function arguments
        no_return_value: If True, don't log return values
        filter_sensitive: If None, uses project-wide setting. If True/False, overrides project setting.
    """

    def func(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                # --- 1. Handle Input Arguments ---
                if not no_input_args:
                    should_filter = (
                        _filtering_enabled
                        if filter_sensitive is None
                        else filter_sensitive
                    )

                    if should_filter:
                        # Use safe serializer with depth=0
                        safe_args = _data_filter.safe_serialize_data(
                            args, current_depth=0
                        )
                        safe_kwargs = _data_filter.safe_serialize_data(
                            kwargs, current_depth=0
                        )
                        span.set_attribute("args", str(safe_args))
                        span.set_attribute("kwargs", str(safe_kwargs))
                    else:
                        # Raw logging (careful: this might still contain QuerySets
                        # if filtering is OFF, but we assume user knows what they are doing)
                        span.set_attribute("args", str(args))
                        span.set_attribute("kwargs", str(kwargs))

                # --- 2. Execute Function ---
                ret = f(*args, **kwargs)

                # --- 3. Handle Return Value ---
                if not no_return_value:
                    should_filter = (
                        _filtering_enabled
                        if filter_sensitive is None
                        else filter_sensitive
                    )

                    # Calculate if we should log returns based on config
                    should_log_return = True
                    if should_filter and not _data_filter.log_return_values:
                        should_log_return = False

                    if should_log_return:
                        if should_filter:
                            safe_ret = _data_filter.safe_serialize_data(
                                ret, current_depth=0
                            )
                            span.set_attribute("return", str(safe_ret))
                        else:
                            span.set_attribute("return", str(ret))

                return ret

        return wrapped

    return func
