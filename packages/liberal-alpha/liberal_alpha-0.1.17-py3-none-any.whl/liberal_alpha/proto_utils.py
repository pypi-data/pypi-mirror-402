from __future__ import annotations

from typing import Any, List, Type


def parse_length_prefixed_messages(payload: bytes, msg_cls: Type[Any]) -> List[Any]:
    """
    Parse a byte payload containing repeated records of:
      4 bytes big-endian unsigned length + protobuf message bytes.

    This is intentionally a small, dependency-light helper so it can be used
    without importing the full client (which has heavier crypto deps).
    """
    rows: List[Any] = []
    if not payload:
        return rows
    offset = 0
    total = len(payload)
    while offset + 4 <= total:
        length = int.from_bytes(payload[offset : offset + 4], byteorder="big", signed=False)
        offset += 4
        if length <= 0:
            continue
        if offset + length > total:
            break
        msg = msg_cls()
        msg.ParseFromString(payload[offset : offset + length])
        offset += length
        rows.append(msg)
    return rows

