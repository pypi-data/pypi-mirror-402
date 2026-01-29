"""
Generated protobuf modules shipped with the SDK.

We intentionally check in the generated python code (e.g. data_entry_pb2.py)
so users do NOT need protoc / .proto files at runtime.

This module is also kept lightweight via lazy imports: importing
`liberal_alpha.proto.data_entry_pb2` should not require `grpcio`.
"""

from __future__ import annotations

from typing import Any

__all__ = ["service_pb2", "service_pb2_grpc", "data_entry_pb2"]


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in ("service_pb2", "service_pb2_grpc", "data_entry_pb2"):
        from importlib import import_module

        return import_module(f"{__name__}.{name}")
    raise AttributeError(name)


