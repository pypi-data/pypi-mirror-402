from __future__ import annotations

from typing import List

from xq_cloud.backend import XQCloudBackend
from xq_cloud.client import HttpSession, XQCloudClient
from xq_cloud.local_backend import XQLocalBackend
from xq_cloud.schemas import BackendInfo
from xq_cloud.util import deserialize_target


class XQCloudProvider:
    """
    For an overview of providers and backends in Qiskit see https://quantum.cloud.ibm.com/docs/en/api/qiskit/providers
    """

    client: XQCloudClient

    def __init__(self, token: str, base_url: str = "https://api.xqool.com", session: HttpSession | None = None):
        super().__init__()
        self.client = XQCloudClient(base_url=base_url, api_key=token, session=session)

    def backends(self, name: str | None = None) -> List[XQCloudBackend]:
        backend_specs = self.client.list_backends()

        xq_backends: List[XQCloudBackend] = []
        for spec in backend_specs:
            if not isinstance(spec, BackendInfo):
                raise TypeError("Expected BackendInfo instances from client.list_backends")

            target = deserialize_target(spec.target)
            description = spec.description or ""
            backend_version = spec.backend_version or "0.0.0"
            supports_pulse_level = spec.supports_pulse_level or False

            backend = XQCloudBackend(
                client=self.client,
                target=target,
                name=spec.name,
                description=description,
                backend_version=str(backend_version),
                supports_pulse_level=supports_pulse_level,
            )
            xq_backends.append(backend)

        if name is not None:
            xq_backends = [backend for backend in xq_backends if backend.name == name]

        return xq_backends


class XQLocalProvider:
    """Local-only provider exposing simulated backends without HTTP calls."""

    def __init__(self, backend_specs: List[BackendInfo | dict]):
        self._backend_specs: List[BackendInfo] = [
            spec if isinstance(spec, BackendInfo) else BackendInfo.model_validate(spec) for spec in backend_specs
        ]
        self._backends = [self._build_backend(spec) for spec in self._backend_specs]

    def _build_backend(self, spec: BackendInfo) -> XQLocalBackend:
        target = deserialize_target(spec.target)
        description = spec.description or ""
        backend_version = spec.backend_version or "0.0.0"
        supports_pulse_level = spec.supports_pulse_level or False

        return XQLocalBackend(
            target=target,
            name=spec.name,
            description=description,
            backend_version=str(backend_version),
            supports_pulse_level=supports_pulse_level,
        )

    def backends(self, name: str | None = None) -> List[XQLocalBackend]:
        xq_backends = self._backends
        if name is not None:
            xq_backends = [backend for backend in xq_backends if backend.name == name]
        return xq_backends
