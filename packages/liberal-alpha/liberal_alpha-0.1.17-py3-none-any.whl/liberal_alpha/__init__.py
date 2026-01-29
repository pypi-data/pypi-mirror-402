"""
Top-level package exports.

Important: keep this module lightweight. Some environments may want to import
submodules (e.g. `liberal_alpha.proto.data_entry_pb2`) without having the full
crypto stack installed (eth-account, etc). We therefore lazily import the heavy
client on attribute access.
"""

from __future__ import annotations

from typing import Any

__all__ = ["LiberalAlphaClient", "initialize", "liberal"]


def __getattr__(name: str) -> Any:  # pragma: no cover
    if name in ("LiberalAlphaClient", "initialize", "liberal"):
        from .client import LiberalAlphaClient, initialize, liberal

        return {"LiberalAlphaClient": LiberalAlphaClient, "initialize": initialize, "liberal": liberal}[name]
    raise AttributeError(name)

