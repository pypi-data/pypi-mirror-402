from recurvedata.client import Client
from recurvedata.core.tracing import Tracing


def create_dp_tracer(service: str) -> Tracing:
    if not Tracing.is_instantiated():
        client = Client()
        kwargs = {}
        client.prepare_header(kwargs)
        tracer = Tracing()
        tracer.init(endpoint=f"{client._config.server_url}/api/tracing/traces", service=service)
        tracer.set_auth_headers(kwargs["headers"])
        return tracer
    return Tracing()
