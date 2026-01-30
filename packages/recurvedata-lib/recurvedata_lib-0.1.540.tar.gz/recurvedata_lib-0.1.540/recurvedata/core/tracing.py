import asyncio
import functools
import inspect
import json
import random
import re
from typing import Any, Dict, overload

from opentelemetry import context, trace
from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel

from .consts import TRACE_KEY, TRACING_CONTEXT_KEY


class _OTLPSpanExporter(OTLPSpanExporter):
    def update_auth_headers(self, headers: Dict[str, str]):
        if not headers:
            return
        self._session.headers.update(headers)


class FilteringSpanProcessor(BatchSpanProcessor):
    """A span processor that filters out unwanted spans before they are created."""

    def __init__(
        self,
        span_exporter: SpanExporter,
        max_queue_size: int = None,
        schedule_delay_millis: float = None,
        max_export_batch_size: int = None,
        export_timeout_millis: float = None,
    ):
        super().__init__(
            span_exporter,
            schedule_delay_millis=schedule_delay_millis,
            export_timeout_millis=export_timeout_millis,
            max_export_batch_size=max_export_batch_size,
            max_queue_size=max_queue_size,
        )
        # Single compiled pattern with OR operator for better performance
        self._fastapi_pattern = re.compile(r"^(?:handling\s+event|Event\s+.*\s+dispatched$)")

    def _should_filter_span(self, span: Span) -> bool:
        """Determine if a span should be filtered out using regex pattern."""
        if not span.name:
            return False
        return bool(self._fastapi_pattern.match(span.name))

    def on_end(self, span: Span) -> None:
        """Called when a span is ended."""
        if not self._should_filter_span(span):
            super().on_end(span)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Tracing(metaclass=Singleton):
    @classmethod
    def is_instantiated(cls):
        """
        Returns the valid singleton instance if it exists, otherwise None.
        """
        instance: "Tracing" = cls._instances.get(cls, None)
        if not instance:
            return False
        if not instance.tracer:
            return False
        return True

    def __init__(
        self,
        endpoint: str = None,
        service: str = None,
        export_timeout_millis: int = 1000,
        schedule_delay_millis: int = 1000,
    ):
        if endpoint and service:
            self.init(endpoint, service, export_timeout_millis, schedule_delay_millis)
        else:
            self.exporter = None
            self.tracer = None

    def init(
        self,
        endpoint: str,
        service: str,
        export_timeout_millis: int = 1000,
        schedule_delay_millis: int = 1000,
    ):
        self.exporter = _OTLPSpanExporter(endpoint=endpoint)
        processor = FilteringSpanProcessor(
            self.exporter, schedule_delay_millis=schedule_delay_millis, export_timeout_millis=export_timeout_millis
        )
        resource = Resource.create(attributes={SERVICE_NAME: service})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(service, tracer_provider=provider)

    def set_auth_headers(self, headers: Dict[str, str]):
        self.exporter.update_auth_headers(headers)

    def dump_context(self) -> Dict[str, str]:
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        return carrier

    def load_context(self, ctx_json: Dict[str, str] | None = None) -> Context:
        ctx = TraceContextTextMapPropagator().extract(ctx_json or {})
        context.attach(ctx)

    def send_context(self, payload: dict):
        payload[TRACE_KEY] = self.dump_context()
        return payload

    @overload
    def receive_context(self, payload: dict):
        ...

    @overload
    def receive_context(self, payload: str):
        ...

    @overload
    def receive_context(self, payload: Any):
        ...

    def receive_context(self, payload: str | dict | BaseModel | Any):
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                return
        elif isinstance(payload, BaseModel):
            payload = payload.model_dump(by_alias=True)
            if not payload.get(TRACING_CONTEXT_KEY, None):
                return
            payload = payload.get(TRACING_CONTEXT_KEY)
            try:
                payload = json.loads(payload)
            except Exception:
                return
        elif isinstance(payload, dict):
            pass
        else:
            from fastapi import Request

            if isinstance(payload, Request):
                payload = payload.headers
            else:
                return

        if TRACE_KEY in payload:
            self.load_context(payload.get(TRACE_KEY))

    def create_span(self, name: str = None, sampling_rate: float = 0.0, context_payload_name: str = None):
        """
        Decorator to create a span for a function.

        Args:
            name: The name of the span. If not provided, the function name will be used.
            sampling_rate: The rate at which to sample the span. Default is 0.0.
            context_payload_name: The name of the argument that contains the context payload."""

        def decorator(func):
            def get_all_args_as_dict(func, args, kwargs):
                """Helper to get all arguments as a dictionary."""
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                return dict(bound_args.arguments)

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                all_args = get_all_args_as_dict(func, args, kwargs)
                if not self.tracer:
                    return await func(*args, **kwargs)
                if context_payload_name:
                    if all_args.get(context_payload_name, None):
                        self.receive_context(all_args[context_payload_name])
                span_name = name or f"{func.__module__}.{func.__name__}"
                if not context.get_current():
                    if random.random() > sampling_rate:
                        return await func(*args, **kwargs)
                with self.tracer.start_as_current_span(span_name):
                    return await func(*args, **kwargs)

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                all_args = get_all_args_as_dict(func, args, kwargs)
                if not self.tracer:
                    return func(*args, **kwargs)
                if context_payload_name:
                    if all_args.get(context_payload_name, None):
                        self.receive_context(all_args[context_payload_name])
                span_name = name or f"{func.__module__}.{func.__name__}"
                if not context.get_current():
                    if random.random() > sampling_rate:
                        return func(*args, **kwargs)
                with self.tracer.start_as_current_span(span_name):
                    return func(*args, **kwargs)

            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

        return decorator

    @property
    def current_span(self) -> Span:
        return trace.get_current_span()
